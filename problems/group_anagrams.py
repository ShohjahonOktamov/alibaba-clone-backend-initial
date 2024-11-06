def group_anagrams(words: list[str]) -> int:
    hash_map: dict[str, list[str]] = {}

    for word in words:
        key: str = ''.join(sorted(word))

        if key not in hash_map:
            hash_map[key]: list[str] = []
        hash_map[key].append(word)

    return len(hash_map)


# bu kodlargaga tegmang

input_str: str = input().strip()
arr: list[str] = list(map(str.strip, input_str.split(',')))
print(group_anagrams(words=arr))
