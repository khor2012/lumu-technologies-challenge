from timestamp_parser import parse_timestamp


def test_parse_timestamp():
    with open('input.txt') as f:
        for line in f.readlines():
            content, expected = line.split(",")
            content = content.replace("'", "")
            expected = expected.replace("\n", "")
            try:
                content = int(content)
            except ValueError:
                pass
            parsed = parse_timestamp(content)

            print(f"val: {content}\nin : {expected}\nout: {parsed}\n")


if __name__ == '__main__':
    test_parse_timestamp()
