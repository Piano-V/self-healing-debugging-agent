from target_code import merge_intervals
// Write your test cases here

def test_empty_intervals():
    assert merge_intervals([]) == []


def test_single_interval():
    assert merge_intervals([[1, 3]]) == [[1, 3]]


def test_standard_merge():
    # Regular overlapping intervals
    assert merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [
        [1, 6],
        [8, 10],
        [15, 18],
    ]


def test_boundary_touching_merge():
    # Boundary matches (e.g., [1, 2] and [2, 3] should merge to [1, 3])
    assert merge_intervals([[1, 2], [2, 3]]) == [[1, 3]]


def test_unsorted_intervals():
    # Out of order intervals
    assert merge_intervals([[8, 10], [1, 3], [2, 6], [15, 18]]) == [
        [1, 6],
        [8, 10],
        [15, 18],
    ]


def test_fully_contained_intervals():
    assert merge_intervals([[1, 4], [2, 3]]) == [[1, 4]]
