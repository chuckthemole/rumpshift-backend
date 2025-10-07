"""
views.py

API endpoints for Counter session data.

Uses:
- shared.api.api_client.ApiClient for external API calls
- shared.logger.logger.get_logger for structured logging
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import pandas as pd
from shared.api.api_client import ApiClient
from shared.logger.logger import get_logger

# -----------------------------------------------------------------------------
# Logger
# -----------------------------------------------------------------------------
logger = get_logger(__name__)

# -----------------------------------------------------------------------------
# Counter Session Data View
# -----------------------------------------------------------------------------


class CounterSessionDataView(APIView):
    """
    Returns counter session data with flexible grouping and aggregation options.

    Query parameters:
        - view: display mode / grouping option
            * "default" -> group by User, sum numeric fields (default)
            * "user" -> each user, multiple entries allowed, sorted alphabetically by user
            * "date" -> entries sorted by Begin Timestamp ascending
            * "user_date" -> group by user but keep individual entries sorted by date
            * "raw" -> no grouping, return all entries as-is
        - agg: aggregation type for Count/Duration ("sum", "mean", "max", "min")
        - limit: optional number of rows to return
        - user: optional, comma-separated list of users to filter
        - start: optional start date (ISO format)
        - end: optional end date (ISO format)
    """

    BASE_URL = "http://localhost:8888"
    ENDPOINT = "/notion-api/integrations/notion/consoleIntegration/database"

    def get(self, request):
        # -------------------------------
        # Parse query parameters
        # -------------------------------
        view_mode = request.query_params.get("view", "default")
        agg = request.query_params.get("agg", "sum")
        limit = request.query_params.get("limit")
        users = request.query_params.get("user")
        start_date = request.query_params.get("start")
        end_date = request.query_params.get("end")

        # Validate limit parameter
        if limit:
            try:
                limit = int(limit)
            except ValueError:
                logger.warning("Invalid limit parameter: %s", limit)
                return Response({"error": "Invalid limit"}, status=status.HTTP_400_BAD_REQUEST)

        # Parse comma-separated users
        if users:
            users = [u.strip() for u in users.split(",")]

        # -------------------------------
        # Fetch data from external API
        # -------------------------------
        api_client = ApiClient(
            name="SpringBootNotionAPI", base_url=self.BASE_URL)
        api_client.set_endpoint(self.ENDPOINT)

        try:
            payload = {"name": "leaderboard"}
            raw_data = api_client.get(params=payload)
            logger.info("Fetched counter session data successfully",
                        count=len(raw_data))
        except Exception:
            logger.exception("Failed to fetch counter session data")
            return Response({"error": "Failed to fetch data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # -------------------------------
        # Flatten Notion results
        # -------------------------------
        results = raw_data.get("results", []) if isinstance(
            raw_data, dict) else []
        flat_data = []

        for page in results:
            props = page.get("properties", {})
            if not props:
                continue

            flat_item = {
                "User": None,
                "Count": None,
                "Duration": None,
                "Begin Timestamp": None,
                "End Timestamp": None
            }

            # Extract User
            title_list = props.get("User", {}).get("title", [])
            if title_list and isinstance(title_list, list):
                flat_item["User"] = title_list[0].get("plain_text")

            # Extract numeric fields
            flat_item["Count"] = props.get("Count", {}).get("number")
            flat_item["Duration"] = props.get("Duration", {}).get("number")

            # Extract timestamps
            flat_item["Begin Timestamp"] = props.get(
                "Start Timestamp", {}).get("date", {}).get("start")
            flat_item["End Timestamp"] = props.get(
                "End Timestamp", {}).get("date", {}).get("start")

            flat_data.append(flat_item)

        logger.info("Flattened data count: %d", len(flat_data))

        # -------------------------------
        # Convert to DataFrame
        # -------------------------------
        df = pd.DataFrame(flat_data)

        # -------------------------------
        # Transform data based on view mode
        # -------------------------------
        try:
            df_transformed = self.transform_data(
                df=df,
                users=users,
                start_date=start_date,
                end_date=end_date,
                agg=agg,
                limit=limit,
                view_mode=view_mode
            )
        except ValueError as ve:
            logger.warning("Data transformation error: %s", ve)
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception("Unexpected error during data transformation")
            return Response({"error": "Failed to process data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # -------------------------------
        # Return JSON response
        # -------------------------------
        response_data = df_transformed.to_dict(orient="records")
        logger.info("Returning %d records after transformation",
                    len(response_data))
        return Response(response_data)

    # -----------------------------------------------------------------------------
    # Data Transformation Helper
    # -----------------------------------------------------------------------------
    def transform_data(self, df, users=None, start_date=None, end_date=None, agg="sum", limit=None, view_mode="default"):
        """
        Apply filtering, grouping, sorting, aggregation, and limiting to the DataFrame.

        Raises ValueError for invalid dates or aggregation functions.
        """
        # Convert timestamp columns to datetime
        for col in ["Begin Timestamp", "End Timestamp"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # -------------------------------
        # Filter by users
        # -------------------------------
        if users and "User" in df.columns:
            df = df[df["User"].isin(users)]

        # -------------------------------
        # Filter by date range
        # -------------------------------
        if start_date and "Begin Timestamp" in df.columns:
            try:
                start_dt = pd.to_datetime(start_date)
                df = df[df["Begin Timestamp"] >= start_dt]
            except Exception:
                raise ValueError(f"Invalid start date: {start_date}")

        if end_date and "End Timestamp" in df.columns:
            try:
                end_dt = pd.to_datetime(end_date)
                df = df[df["End Timestamp"] <= end_dt]
            except Exception:
                raise ValueError(f"Invalid end date: {end_date}")

        # -------------------------------
        # Apply aggregation / grouping based on view_mode
        # -------------------------------
        numeric_cols = [col for col in [
            "Count", "Duration"] if col in df.columns]

        if view_mode == "default":
            # Default: group by User, sum numeric fields
            if "User" in df.columns:
                df = df.groupby("User", as_index=False)[numeric_cols].agg(agg)

        elif view_mode == "user":
            # User alphabetical, keep individual entries
            df = df.sort_values(by=["User", "Begin Timestamp"])

        elif view_mode == "date":
            # Entries sorted by Begin Timestamp ascending
            df = df.sort_values(by=["Begin Timestamp"])

        elif view_mode == "user_date":
            # Group by user, but keep individual entries sorted by date
            df = df.sort_values(by=["User", "Begin Timestamp"])

        elif view_mode == "raw":
            # Return all entries as-is
            pass

        else:
            raise ValueError(f"Invalid view_mode: {view_mode}")

        # -------------------------------
        # Apply limit
        # -------------------------------
        if limit:
            df = df.head(limit)

        return df
