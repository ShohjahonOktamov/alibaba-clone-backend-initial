def can_construct(ransomNote: str, magazine: str) -> bool:
    for char in set(ransomNote):
        if ransomNote.count(char) > magazine.count(char):
            return False
    return True


# bu kodlargaga tegmang

input_str: str = input().strip()
wransomNote, magazine = input_str.split('|')
print(can_construct(wransomNote, magazine))
