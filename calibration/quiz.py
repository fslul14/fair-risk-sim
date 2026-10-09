"""Calibration practice: give a 90% confidence interval for each quantity.

If you are well calibrated, about 9 of 10 true values land inside your ranges.
Most people start well below that (ranges too narrow). Practice with a fresh set each time,
because you cannot retake a set whose answers you have already seen.

Usage
    python3 calibration/quiz.py --set 1   # the original 10 questions
    python3 calibration/quiz.py --set 2   # 20 new questions
Each run appends your score to calibration/calibration_log.csv so you can track progress.
"""

import argparse
import csv
import datetime
from pathlib import Path

QUESTION_SETS = {
    1: [
        ("Height of Mount Everest (meters)", 8849),
        ("Average distance from Earth to the Moon (km)", 384_400),
        ("Number of bones in an adult human body", 206),
        ("Year the Magna Carta was sealed", 1215),
        ("Year the first iPhone was released", 2007),
        ("Height of the Burj Khalifa (meters)", 828),
        ("Year Wikipedia was launched", 2001),
        ("Age of the Earth (billions of years)", 4.54),
        ("Main span of the Golden Gate Bridge (meters)", 1280),
        ("Speed of sound in air at sea level, 15 C (meters per second)", 340),
    ],
    2: [
        ("Year the Berlin Wall fell", 1989),
        ("Number of moons orbiting Mars", 2),
        ("Average distance from Earth to the Sun (millions of km)", 149.6),
        ("Height of the Statue of Liberty, ground to torch tip (meters)", 93),
        ("Year the Suez Canal opened", 1869),
        ("Length of a marathon (km)", 42.195),
        ("Year the Eiffel Tower was completed", 1889),
        ("Year the first Nobel Prizes were awarded", 1901),
        ("Surface temperature of the Sun (kelvin)", 5772),
        ("Maximum depth of Lake Baikal (meters)", 1642),
        ("Number of officially recognized chemical elements", 118),
        ("Height of Mount Kilimanjaro (meters)", 5895),
        ("Year of the Wright brothers' first powered flight", 1903),
        ("Length of a Martian year (Earth days)", 687),
        ("Height of Mount Fuji (meters)", 3776),
        ("Mean diameter of the Earth (km)", 12_742),
        ("Length of the Panama Canal (km)", 82),
        ("Year of the Apollo 11 Moon landing", 1969),
        ("Year the Colosseum in Rome opened (AD)", 80),
        ("Olympic gold medals won by Michael Phelps", 23),
    ],
}

LOG_PATH = Path(__file__).with_name("calibration_log.csv")


def ask(prompt: str) -> float:
    while True:
        try:
            return float(input(prompt).replace(",", ""))
        except ValueError:
            print("  enter a number")


def log_score(set_number: int, hits: int, total: int) -> None:
    new_file = not LOG_PATH.exists()
    with LOG_PATH.open("a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["date", "set", "hits", "questions"])
        writer.writerow([datetime.date.today().isoformat(), set_number, hits, total])


def main() -> None:
    parser = argparse.ArgumentParser(description="90% confidence interval calibration quiz")
    parser.add_argument("--set", type=int, default=1, choices=sorted(QUESTION_SETS), help="question set")
    args = parser.parse_args()
    questions = QUESTION_SETS[args.set]

    print(f"Set {args.set}: {len(questions)} questions.")
    print("For each, enter a LOW and HIGH so you are 90% sure the true value is between them.")
    print("Tip: start from a range that feels absurdly wide, then narrow only for specific reasons.\n")

    hits = 0
    for i, (question, truth) in enumerate(questions, 1):
        print(f"{i}. {question}")
        low = ask("   low:  ")
        high = ask("   high: ")
        low, high = min(low, high), max(low, high)
        hit = low <= truth <= high
        hits += hit
        print(f"   answer: {truth:,}  ->  {'inside' if hit else 'MISSED'}\n")

    total = len(questions)
    target = round(0.9 * total)
    print(f"Score: {hits}/{total} inside your ranges (target: about {target}).")
    if hits < target - 1:
        print("Overconfident: your ranges were too narrow. Ask 'what would have to be true for the "
              "value to be outside this range?' and widen until that feels unlikely.")
    elif hits == total:
        print("A perfect score can mean ranges too wide to be useful. Aim to miss about one in ten.")
    else:
        print("Close to calibrated. Calibration is a habit, so repeat it with a fresh set later.")
    log_score(args.set, hits, total)
    print(f"Logged to {LOG_PATH.name}")


if __name__ == "__main__":
    main()