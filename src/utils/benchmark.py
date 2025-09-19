import time
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from models.models import Benchmark


class BenchmarkManager:
    """Manager for recording operation benchmarks."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def record_benchmark(
        self,
        operation_type: str,
        operation_name: str,
        start_time: datetime,
        end_time: datetime,
        status: str = "success",
        region: Optional[str] = None,
        record_count: Optional[int] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a benchmark entry in the database."""
        duration = (end_time - start_time).total_seconds()
        
        benchmark = Benchmark(
            operation_type=operation_type,
            operation_name=operation_name,
            region=region,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            record_count=record_count,
            status=status,
            error_message=error_message,
            metadata=metadata,
        )
        
        self.session.add(benchmark)
        self.session.commit()

    @contextmanager
    def benchmark_operation(
        self,
        operation_type: str,
        operation_name: str,
        region: Optional[str] = None,
        record_count: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Context manager for timing operations."""
        start_time = datetime.now(UTC)
        status = "success"
        error_message = None
        
        try:
            yield
        except Exception as e:
            status = "failed"
            error_message = str(e)
            raise
        finally:
            end_time = datetime.now(UTC)
            self.record_benchmark(
                operation_type=operation_type,
                operation_name=operation_name,
                start_time=start_time,
                end_time=end_time,
                status=status,
                region=region,
                record_count=record_count,
                error_message=error_message,
                metadata=metadata,
            )


def benchmark_decorator(
    operation_type: str,
    operation_name: str,
    region: Optional[str] = None,
):
    """Decorator for timing functions with database recording."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Try to find a session in the args/kwargs
            session = None
            for arg in args:
                if isinstance(arg, Session):
                    session = arg
                    break
            
            if session is None:
                # If no session found, just run the function without benchmarking
                return func(*args, **kwargs)
            
            benchmark_manager = BenchmarkManager(session)
            
            with benchmark_manager.benchmark_operation(
                operation_type=operation_type,
                operation_name=operation_name,
                region=region,
            ):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator
