
from fastapi import APIRouter
from sqlalchemy import inspect, MetaData, Table, select, func

from app.database import engine

router = APIRouter(
    prefix="/system",
    tags=["System"]
)


@router.get("/tables")
def get_database_tables():
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    return {
        "database": "academic_integrity",
        "total_tables": len(tables),
        "tables": tables
    }


@router.get("/schema")
def get_database_schema():
    inspector = inspect(engine)
    schema = {}

    for table_name in inspector.get_table_names():
        schema[table_name] = {
            "columns": [
                {
                    "name": column["name"],
                    "type": str(column["type"]),
                    "nullable": column["nullable"],
                    "primary_key": column.get("primary_key", False)
                }
                for column in inspector.get_columns(table_name)
            ],
            "foreign_keys": inspector.get_foreign_keys(table_name)
        }

    return schema


@router.get("/summary")
def get_database_summary():
    metadata = MetaData()
    inspector = inspect(engine)

    result = {}

    with engine.connect() as connection:
        for table_name in inspector.get_table_names():
            table = Table(
                table_name,
                metadata,
                autoload_with=engine
            )

            query = select(func.count()).select_from(table)

            result[table_name] = connection.execute(
                query
            ).scalar_one()

    return {
        "total_tables": len(result),
        "table_counts": result
    }
