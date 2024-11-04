def find_words(words: list[str]) -> list[str]:
    result: set[str] = set()

    for word in words:
        if word not in result:
            if word[0].lower() in "zxcvbnm":
                row: str = "zxcvbnm"
            elif word[0].lower() in "asdfghjkl":
                row: str = "asdfghjkl"
            else:
                row: str = "qwertyuiop"

            for letter in word[1:]:
                if letter.lower() not in row:
                    break
            else:
                result.add(word)

    return list(sorted(result))


# bu kodlargaga tegmang

input_str: str = input().strip()
arr: list[str] = list(map(str.strip, input_str.split(',')))
print(find_words(arr))
