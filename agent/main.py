from collectors.cpu import get_cpu_usage


def main():
    cpu_usage = get_cpu_usage()

    print(f"CPU Usage: {cpu_usage}%")


if __name__ == "__main__":
    main()