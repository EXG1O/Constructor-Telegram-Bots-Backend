from typing import Any


def deep_merge_data(target: Any, source: Any) -> Any:
    if isinstance(target, dict) and isinstance(source, dict):
        result: dict[str, Any] = target.copy()
        result.update(
            {
                key: deep_merge_data(result[key], value) if key in result else value
                for key, value in source.items()
            }
        )
        return result
    elif isinstance(target, list):
        return target + (source if isinstance(source, list) else [source])

    return source
