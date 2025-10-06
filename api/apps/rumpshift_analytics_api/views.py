from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import pandas as pd
from datetime import datetime


class ExampleDataView(APIView):
    """
    Returns sample analytics data as JSON.
    Template for future endpoints.
    """

    def get(self, request):
        # Sample DataFrame
        df = pd.DataFrame({
            'month': ['Jan', 'Feb', 'Mar', 'Apr'],
            'sales': [100, 150, 120, 170]
        })

        data = {
            'labels': df['month'].tolist(),
            'values': df['sales'].tolist()
        }

        return Response(data)


class CounterSessionDataView(APIView):
    """
    Returns counter session data with flexible organization options.
    Query parameters:
        - group_by: column to group by ("User", "Begin Timestamp", etc.)
        - agg: aggregation type for Count/Duration ("sum", "mean", "max", "min")
        - limit: optional number of rows to return
        - user: optional, comma-separated list of users to filter
        - start: optional start date (ISO format)
        - end: optional end date (ISO format)
    """

    def get(self, request):
        # -------------------------------
        # 1️⃣ Parse query params
        # -------------------------------
        group_by = request.query_params.get("group_by")
        agg = request.query_params.get("agg", "sum")
        limit = request.query_params.get("limit")
        users = request.query_params.get("user")
        start_date = request.query_params.get("start")
        end_date = request.query_params.get("end")

        if limit:
            try:
                limit = int(limit)
            except ValueError:
                return Response({"error": "Invalid limit"}, status=status.HTTP_400_BAD_REQUEST)

        if users:
            users = [u.strip() for u in users.split(",")]

        # -------------------------------
        # 2️⃣ Fetch data from external API (stub)
        # -------------------------------
        data = [
            {"User": "Alice", "Count": 5, "Duration": 120, "Begin Timestamp": "2025-10-01T10:00:00",
             "End Timestamp": "2025-10-01T12:00:00", "Notes": "Test 1"},
            {"User": "Bob", "Count": 3, "Duration": 60, "Begin Timestamp": "2025-10-01T11:00:00",
             "End Timestamp": "2025-10-01T12:00:00", "Notes": "Test 2"},
            {"User": "Alice", "Count": 2, "Duration": 30, "Begin Timestamp": "2025-10-02T09:00:00",
             "End Timestamp": "2025-10-02T09:30:00", "Notes": "Test 3"},
        ]

        df = pd.DataFrame(data)

        # Convert timestamps to datetime
        df["Begin Timestamp"] = pd.to_datetime(df["Begin Timestamp"])
        df["End Timestamp"] = pd.to_datetime(df["End Timestamp"])

        # -------------------------------
        # 3️⃣ Apply filters
        # -------------------------------
        if users:
            df = df[df["User"].isin(users)]

        if start_date:
            try:
                start_dt = pd.to_datetime(start_date)
                df = df[df["Begin Timestamp"] >= start_dt]
            except Exception:
                return Response({"error": "Invalid start date"}, status=status.HTTP_400_BAD_REQUEST)

        if end_date:
            try:
                end_dt = pd.to_datetime(end_date)
                df = df[df["End Timestamp"] <= end_dt]
            except Exception:
                return Response({"error": "Invalid end date"}, status=status.HTTP_400_BAD_REQUEST)

        # -------------------------------
        # 4️⃣ Apply aggregation
        # -------------------------------
        numeric_cols = ["Count", "Duration"]
        if group_by and group_by in df.columns:
            if agg not in ["sum", "mean", "max", "min"]:
                return Response({"error": f"Invalid aggregation: {agg}"}, status=status.HTTP_400_BAD_REQUEST)

            agg_func = getattr(df[numeric_cols].groupby(df[group_by]), agg)
            df_agg = agg_func().reset_index()
        else:
            df_agg = df

        # -------------------------------
        # 5️⃣ Apply limit
        # -------------------------------
        if limit:
            df_agg = df_agg.head(limit)

        # -------------------------------
        # 6️⃣ Return JSON
        # -------------------------------
        return Response(df_agg.to_dict(orient="records"))
