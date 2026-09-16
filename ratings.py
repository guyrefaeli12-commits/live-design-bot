"""
Professional Design Rating System
==================================

Stores and manages user ratings for generated designs.

Features:
- 1–5 star ratings
- One rating per user per design
- Rating updates
- Average score calculation
- Total rating count
- Design statistics
- Persistent JSON storage
- Safe file handling
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

RATINGS_FILE = DATA_DIR / "ratings.json"

logger = logging.getLogger("LiveDesignStudio.Ratings")


# ============================================================
# RATING DATABASE
# ============================================================

class RatingDatabase:
    """
    Lightweight persistent rating database.

    JSON is used for the first version so the bot can run
    easily on Render without requiring a separate database.

    The architecture is intentionally isolated so we can later
    replace JSON with SQLite/PostgreSQL without changing the
    Discord command layer.
    """

    def __init__(
        self,
        file_path: str | Path = RATINGS_FILE,
    ):
        self.file_path = Path(file_path)
        self.lock = threading.RLock()

        self._ensure_database()

    # --------------------------------------------------------
    # Database Initialization
    # --------------------------------------------------------

    def _ensure_database(self) -> None:

        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self.file_path.exists():

            self._write_data(
                {
                    "version": 1,
                    "ratings": [],
                }
            )

    # --------------------------------------------------------
    # File Operations
    # --------------------------------------------------------

    def _read_data(self) -> dict[str, Any]:

        with self.lock:

            try:

                with self.file_path.open(
                    "r",
                    encoding="utf-8",
                ) as file:

                    data = json.load(file)

                if not isinstance(data, dict):
                    raise ValueError(
                        "Rating database must contain an object."
                    )

                if "ratings" not in data:
                    data["ratings"] = []

                return data

            except FileNotFoundError:

                return {
                    "version": 1,
                    "ratings": [],
                }

            except json.JSONDecodeError as error:

                logger.error(
                    "Invalid ratings database: %s",
                    error,
                )

                # Do not silently destroy existing data.
                raise RuntimeError(
                    "The ratings database contains invalid JSON."
                ) from error

    def _write_data(
        self,
        data: dict[str, Any],
    ) -> None:

        with self.lock:

            temporary_file = self.file_path.with_suffix(
                ".tmp"
            )

            with temporary_file.open(
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    data,
                    file,
                    ensure_ascii=False,
                    indent=2,
                )

                file.flush()

            temporary_file.replace(
                self.file_path
            )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    @staticmethod
    def _validate_rating(
        rating: int,
    ) -> int:

        if isinstance(rating, bool):
            raise ValueError(
                "Rating must be an integer between 1 and 5."
            )

        try:
            rating = int(rating)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "Rating must be an integer."
            ) from error

        if rating < 1 or rating > 5:
            raise ValueError(
                "Rating must be between 1 and 5."
            )

        return rating

    @staticmethod
    def _clean_id(
        value: Any,
        field_name: str,
    ) -> str:

        if value is None:
            raise ValueError(
                f"{field_name} cannot be empty."
            )

        value = str(value).strip()

        if not value:
            raise ValueError(
                f"{field_name} cannot be empty."
            )

        if len(value) > 200:
            raise ValueError(
                f"{field_name} is too long."
            )

        return value

    # --------------------------------------------------------
    # Add / Update Rating
    # --------------------------------------------------------

    def set_rating(
        self,
        design_id: str,
        user_id: str,
        rating: int,
    ) -> dict[str, Any]:

        design_id = self._clean_id(
            design_id,
            "design_id",
        )

        user_id = self._clean_id(
            user_id,
            "user_id",
        )

        rating = self._validate_rating(
            rating
        )

        now = datetime.now(
            timezone.utc
        ).isoformat()

        with self.lock:

            data = self._read_data()

            ratings = data.setdefault(
                "ratings",
                [],
            )

            existing = None

            for item in ratings:

                if (
                    str(item.get("design_id"))
                    == design_id
                    and
                    str(item.get("user_id"))
                    == user_id
                ):
                    existing = item
                    break

            if existing:

                old_rating = existing.get(
                    "rating"
                )

                existing["rating"] = rating
                existing["updated_at"] = now

                action = "updated"

                logger.info(
                    "Updated rating: design=%s user=%s %s->%s",
                    design_id,
                    user_id,
                    old_rating,
                    rating,
                )

            else:

                entry = {
                    "design_id": design_id,
                    "user_id": user_id,
                    "rating": rating,
                    "created_at": now,
                    "updated_at": now,
                }

                ratings.append(entry)

                action = "created"

                logger.info(
                    "Created rating: design=%s user=%s rating=%s",
                    design_id,
                    user_id,
                    rating,
                )

            self._write_data(
                data
            )

        statistics = self.get_design_stats(
            design_id
        )

        return {
            "action": action,
            "design_id": design_id,
            "user_id": user_id,
            "rating": rating,
            "average": statistics["average"],
            "count": statistics["count"],
        }

    # --------------------------------------------------------
    # Get Ratings For Design
    # --------------------------------------------------------

    def get_design_ratings(
        self,
        design_id: str,
    ) -> list[dict[str, Any]]:

        design_id = self._clean_id(
            design_id,
            "design_id",
        )

        data = self._read_data()

        return [
            item
            for item in data.get(
                "ratings",
                [],
            )
            if str(item.get("design_id"))
            == design_id
        ]

    # --------------------------------------------------------
    # Design Statistics
    # --------------------------------------------------------

    def get_design_stats(
        self,
        design_id: str,
    ) -> dict[str, Any]:

        ratings = self.get_design_ratings(
            design_id
        )

        values = []

        for item in ratings:

            try:
                value = int(
                    item.get("rating")
                )

                if 1 <= value <= 5:
                    values.append(value)

            except (
                TypeError,
                ValueError,
            ):
                continue

        count = len(values)

        if count:
            average = round(
                sum(values) / count,
                2,
            )
        else:
            average = 0.0

        distribution = {
            "1": values.count(1),
            "2": values.count(2),
            "3": values.count(3),
            "4": values.count(4),
            "5": values.count(5),
        }

        return {
            "design_id": design_id,
            "average": average,
            "count": count,
            "distribution": distribution,
        }

    # --------------------------------------------------------
    # Global Statistics
    # --------------------------------------------------------

    def get_global_stats(
        self,
    ) -> dict[str, Any]:

        data = self._read_data()

        ratings = data.get(
            "ratings",
            [],
        )

        values = []

        designs = set()
        users = set()

        for item in ratings:

            try:

                value = int(
                    item.get("rating")
                )

                if not 1 <= value <= 5:
                    continue

                values.append(value)

                designs.add(
                    str(
                        item.get(
                            "design_id"
                        )
                    )
                )

                users.add(
                    str(
                        item.get(
                            "user_id"
                        )
                    )
                )

            except (
                TypeError,
                ValueError,
            ):
                continue

        count = len(values)

        average = (
            round(
                sum(values) / count,
                2,
            )
            if count
            else 0.0
        )

        distribution = {
            "1": values.count(1),
            "2": values.count(2),
            "3": values.count(3),
            "4": values.count(4),
            "5": values.count(5),
        }

        return {
            "total_ratings": count,
            "total_designs_rated": len(
                designs
            ),
            "total_users": len(
                users
            ),
            "average": average,
            "distribution": distribution,
        }

    # --------------------------------------------------------
    # User Rating
    # --------------------------------------------------------

    def get_user_rating(
        self,
        design_id: str,
        user_id: str,
    ) -> int | None:

        design_id = self._clean_id(
            design_id,
            "design_id",
        )

        user_id = self._clean_id(
            user_id,
            "user_id",
        )

        ratings = self.get_design_ratings(
            design_id
        )

        for item in ratings:

            if (
                str(item.get("user_id"))
                == user_id
            ):

                try:
                    return int(
                        item.get("rating")
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    return None

        return None

    # --------------------------------------------------------
    # Top Rated Designs
    # --------------------------------------------------------

    def get_top_designs(
        self,
        minimum_ratings: int = 1,
        limit: int = 10,
    ) -> list[dict[str, Any]]:

        minimum_ratings = max(
            1,
            int(minimum_ratings),
        )

        limit = max(
            1,
            min(int(limit), 100),
        )

        data = self._read_data()

        design_ids = {
            str(item.get("design_id"))
            for item in data.get(
                "ratings",
                [],
            )
            if item.get("design_id")
        }

        results = []

        for design_id in design_ids:

            stats = self.get_design_stats(
                design_id
            )

            if (
                stats["count"]
                >= minimum_ratings
            ):
                results.append(
                    stats
                )

        results.sort(
            key=lambda item: (
                item["average"],
                item["count"],
            ),
            reverse=True,
        )

        return results[:limit]

    # --------------------------------------------------------
    # Delete Design Ratings
    # --------------------------------------------------------

    def delete_design(
        self,
        design_id: str,
    ) -> int:

        design_id = self._clean_id(
            design_id,
            "design_id",
        )

        with self.lock:

            data = self._read_data()

            ratings = data.get(
                "ratings",
                [],
            )

            original_count = len(
                ratings
            )

            data["ratings"] = [
                item
                for item in ratings
                if str(
                    item.get("design_id")
                ) != design_id
            ]

            removed = (
                original_count
                - len(data["ratings"])
            )

            self._write_data(
                data
            )

            logger.info(
                "Deleted %s ratings for design %s",
                removed,
                design_id,
            )

            return removed


# ============================================================
# SINGLETON DATABASE
# ============================================================

rating_database = RatingDatabase()


# ============================================================
# PUBLIC FUNCTIONS
# ============================================================

def save_rating(
    design_id: str,
    user_id: str,
    rating: int,
) -> dict[str, Any]:

    return rating_database.set_rating(
        design_id=design_id,
        user_id=user_id,
        rating=rating,
    )


def get_design_stats(
    design_id: str,
) -> dict[str, Any]:

    return rating_database.get_design_stats(
        design_id
    )


def get_global_stats() -> dict[str, Any]:

    return rating_database.get_global_stats()


def get_user_rating(
    design_id: str,
    user_id: str,
) -> int | None:

    return rating_database.get_user_rating(
        design_id,
        user_id,
    )


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("LIVE DESIGN STUDIO - RATING SYSTEM TEST")
    print("=" * 60)

    test_design = "local_test_design"
    test_user = "local_test_user"

    result = save_rating(
        design_id=test_design,
        user_id=test_user,
        rating=5,
    )

    print("\nRating saved:")
    print(result)

    print("\nDesign statistics:")
    print(
        get_design_stats(
            test_design
        )
    )

    print("\nGlobal statistics:")
    print(
        get_global_stats()
    )

    print("\nUser rating:")
    print(
        get_user_rating(
            test_design,
            test_user,
        )
    )

    print("\nRating system is ready.")
