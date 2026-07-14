def merge_intervals(intervals: list[list[int]]) -> list[list[int]]:
    """Merges all overlapping intervals in a list and returns the merged list.

    Bugs:
    1. Forgets to sort the intervals first, which fails on out-of-order lists.
    2. Uses strict `<` instead of `<=` check, failing on adjacent boundaries.
    """
    if not intervals:
        return []

    merged = []

    # BUG: Missing standard sorting step: intervals.sort(key=lambda x: x[0])

    current = intervals[0]
    for next_int in intervals[1:]:
        # BUG: Should check next_int[0] <= current[1] to merge boundary matches
        if next_int[0] < current[1]:
            current[1] = max(current[1], next_int[1])
        else:
            merged.append(current)
            current = next_int

    merged.append(current)
    return merged