import argparse
import time
import requests
from config import TARGET_URL, DEFAULT_REQUESTS_COUNT


def measure_speed(url: str, requests_count: int = 10) -> None:
    print(f"Целевой адрес: {url}")

    headers = {
        "User-Agent": "ConsoleSpeedTest/3.3",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
    }

    with requests.Session() as session:
        # --- 1. РЕШЕНИЕ ПРОБЛЕМЫ TCP SLOW START: Прогревочный запрос ---
        print("Выполняется прогревочный запрос (Warm-up)...")
        try:
            warmup_url = (
                f"{url}&_warmup=1" if "?" in url else f"{url}?_warmup=1"
            )
            session.get(warmup_url, headers=headers, timeout=10, stream=True)
        except Exception as e:
            print(
                f"Предупреждение: прогревочный запрос завершился ошибкой ({e}),"
                " продолжаем..."
            )

        print(
            f"Запуск основных измерений ({requests_count} запросов)...\n"
        )

        total_bytes = 0
        total_download_time = 0.0
        successful_requests = 0

        for i in range(1, requests_count + 1):
            try:
                # --- 2. РЕШЕНИЕ ПРОБЛЕМЫ КЭШИРОВАНИЯ: Cache-busting ---
                separator = "&" if "?" in url else "?"
                target_url = f"{url}{separator}_cb={int(time.time() * 1000)}"

                response = session.get(
                    target_url, headers=headers, timeout=15, stream=True
                )

                if response.status_code != 200:
                    print(
                        f"[{i}/{requests_count}] Пропущено: сервер вернул статус"
                        f" {response.status_code}"
                    )
                    response.close()
                    continue

                # --- 3. РЕШЕНИЕ ПРОБЛЕМЫ TTFB: Раздельный замер ---
                request_bytes = 0
                download_start = time.perf_counter()

                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        request_bytes += len(chunk)

                download_end = time.perf_counter()
                download_time = download_end - download_start

                if download_time <= 0:
                    continue

                total_bytes += request_bytes
                total_download_time += download_time
                successful_requests += 1

                print(
                    f"[{i}/{requests_count}] Размер: {request_bytes / (1024*1024):.2f} МБ"
                    f" | Время скачивания: {download_time:.3f} сек"
                )

            except requests.exceptions.RequestException as e:
                print(f"[{i}/{requests_count}] Ошибка запроса: {e}")

    if successful_requests == 0:
        print("\nНе удалось выполнить ни одного успешного запроса.")
        return

    speed_bytes_per_sec = total_bytes / total_download_time
    speed_mbps = (speed_bytes_per_sec * 8) / (1024 * 1024)

    print("\n" + "=" * 40)
    print("ИТОГИ ТОЧНОГО ТЕСТА:")
    print("=" * 40)
    print(f"Успешных запросов:     {successful_requests} из {requests_count}")
    print(f"Общий объём данных:    {total_bytes / (1024 * 1024):.2f} МБ")
    print(f"Чистое время передачи: {total_download_time:.3f} сек")
    print(
        f"Средняя скорость:      {speed_mbps:.2f} Мбит/с (Mbps)"
        f" | {speed_bytes_per_sec / (1024 * 1024):.2f} МБ/с (MB/s)"
    )
    print("=" * 40)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Профессиональный бенчмарк скорости скачивания."
    )
    parser.add_argument(
        "url",
        nargs="?",
        default=None,
        help=(
            "URL адрес для скачивания (если не указан, берется из config.py)"
        ),
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=None,
        help="Количество запросов",
    )

    args = parser.parse_args()

    url_to_use = args.url if args.url else TARGET_URL
    count_to_use = (
        args.count if args.count is not None else DEFAULT_REQUESTS_COUNT
    )

    measure_speed(url_to_use, count_to_use)
