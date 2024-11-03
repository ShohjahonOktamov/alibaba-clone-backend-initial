def two_sum(nums: list, target: int) -> list[int]:
    hash_map: dict[int, int] = {}

    for i, num in enumerate(nums):
        num2 = target - num
        if num2 in hash_map:
            return [hash_map[num2], i]
        hash_map[num] = i

# bu kodlargaga tegmang

input_str = input().strip()
arr, target = input_str.split('|')
arr = list(map(int, arr.split(',')))
print(two_sum(arr, int(target)))
