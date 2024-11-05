def is_anagram(s: str, t: str) -> bool:
    return sorted(s) == sorted(t)


# bu kodlargaga tegmang

input_str: str = input().strip()
s, t = input_str.split('|')
print(is_anagram(s, t))
