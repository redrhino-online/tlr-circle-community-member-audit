#!/usr/bin/env python3

import argparse
import csv
import os
import pickle
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime
from io import TextIOWrapper
from typing import List, Optional


# -----------------------------
# Domain Layer
# -----------------------------
@dataclass
class Member:
    first_name: str
    last_name: str
    email: str
    join_date: datetime
    profile_url: str


# -----------------------------
# Infrastructure Layer
# -----------------------------
class FileHandler:
    @staticmethod
    def extract_csv_from_zip(zip_path: str) -> TextIOWrapper:
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                # Find the first CSV file in the ZIP
                csv_files = [
                    f for f in zip_ref.namelist() if f.lower().endswith(".csv")
                ]
                if not csv_files:
                    raise FileNotFoundError("No CSV file found inside the ZIP archive.")
                csv_filename = csv_files[0]
                return TextIOWrapper(zip_ref.open(csv_filename), encoding="utf-8")
        except zipfile.BadZipFile:
            raise ValueError("The provided file is not a valid ZIP archive.")

    @staticmethod
    def parse_members(csv_file) -> List[Member]:
        reader = csv.DictReader(csv_file)
        members = []
        for row in reader:
            try:
                join_date = FileHandler.parse_date(row["Join Date"])
            except ValueError as ve:
                raise ValueError(f"Invalid date format in row: {row}") from ve
            member = Member(
                first_name=row.get("First Name", "").strip(),
                last_name=row.get("Last Name", "").strip(),
                email=row.get("Email", "").strip(),
                join_date=join_date,
                profile_url=row.get("Profile URL", "").strip(),
            )
            members.append(member)
        return members

    @staticmethod
    def parse_date(date_str: str) -> datetime:
        """
        Attempts to parse the date string using multiple formats.
        Raises ValueError if none of the formats match.
        """
        date_formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d",  # Fallback format
        ]
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        # If none of the formats match, raise an error
        raise ValueError(f"Date '{date_str}' is not in a recognized format.")


class CacheHandler:
    CACHE_FILE = "last_join_date.pkl"

    @staticmethod
    def load_last_join_date() -> Optional[datetime]:
        if not os.path.exists(CacheHandler.CACHE_FILE):
            return None
        try:
            with open(CacheHandler.CACHE_FILE, "rb") as f:
                return pickle.load(f)
        except (pickle.UnpicklingError, EOFError):
            print(
                "Warning: Cache file is corrupted. It will be ignored.", file=sys.stderr
            )
            return None

    @staticmethod
    def save_last_join_date(join_date: datetime):
        with open(CacheHandler.CACHE_FILE, "wb") as f:
            pickle.dump(join_date, f)


# -----------------------------
# Application Layer
# -----------------------------
class MemberProcessor:
    def __init__(self, file_path: str, reference_date: Optional[datetime] = None):
        self.file_path = file_path
        self.file_handler = FileHandler()
        self.cache_handler = CacheHandler()
        self.provided_reference_date = reference_date

    def process(self) -> List[Member]:
        # Determine if input is ZIP or CSV
        if self.file_path.lower().endswith(".zip"):
            csv_file = self.file_handler.extract_csv_from_zip(self.file_path)
        elif self.file_path.lower().endswith(".csv"):
            try:
                csv_file = open(self.file_path, "r", encoding="utf-8")
            except FileNotFoundError:
                raise FileNotFoundError(f"CSV file '{self.file_path}' not found.")
        else:
            raise ValueError("Input file must be a ZIP or CSV file.")

        with csv_file:
            all_members = self.file_handler.parse_members(csv_file)

        if self.provided_reference_date:
            reference_date = self.provided_reference_date
            print(f"Using provided reference date: {reference_date.isoformat()}Z")
        else:
            last_join_date = self.cache_handler.load_last_join_date()
            if last_join_date:
                reference_date = last_join_date
                print(f"Using cached reference date: {reference_date.isoformat()}Z")
            else:
                reference_date = self.get_user_reference_date()

        if reference_date:
            filtered_members = [m for m in all_members if m.join_date > reference_date]
            print(
                f"Filtered members: {len(filtered_members)} out of {len(all_members)}"
            )
        else:
            filtered_members = all_members
            print(f"Including all members: {len(filtered_members)}")

        if filtered_members:
            latest_date = max(m.join_date for m in filtered_members)
            self.cache_handler.save_last_join_date(latest_date)
            print(f"Updated last join date to: {latest_date.isoformat()}Z")
        else:
            print("No new members to process.")

        return filtered_members

    @staticmethod
    def get_user_reference_date() -> Optional[datetime]:
        while True:
            choice = input(
                "No cached timestamp found. Do you want to (1) Provide a timestamp or (2) Include all members? [1/2]: "
            ).strip()
            if choice == "1":
                timestamp_str = input(
                    "Enter the reference timestamp (YYYY-MM-DD HH:MM:SS or ISO 8601): "
                ).strip()
                try:
                    return FileHandler.parse_date(timestamp_str)
                except ValueError:
                    print("Invalid format. Please try again.", file=sys.stderr)
            elif choice == "2":
                return None
            else:
                print("Invalid choice. Please enter 1 or 2.", file=sys.stderr)


# -----------------------------
# Presentation Layer
# -----------------------------
class CLI:
    @staticmethod
    def write_output(members: List[Member], output_path: str):
        # Sort members by join_date descending
        members_sorted = sorted(members, key=lambda m: m.join_date, reverse=True)

        fieldnames = ["First Name", "Last Name", "Email", "Join Date", "Profile URL"]
        try:
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for member in members_sorted:
                    writer.writerow(
                        {
                            "First Name": member.first_name,
                            "Last Name": member.last_name,
                            "Email": member.email,
                            # Formatting Join Date in ISO 8601 format
                            "Join Date": member.join_date.strftime(
                                "%Y-%m-%dT%H:%M:%SZ"
                            ),
                            "Profile URL": member.profile_url,
                        }
                    )
            print(f"Output written to {output_path}")
        except IOError as e:
            print(f"Failed to write output file: {e}", file=sys.stderr)
            sys.exit(1)

    @staticmethod
    def generate_default_output_filename() -> str:
        current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"output_{current_datetime}.csv"

    @staticmethod
    def parse_arguments() -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            description="Process community members from a ZIP or CSV file."
        )
        parser.add_argument(
            "input",
            type=str,
            help="Path to the ZIP or CSV file containing the members data.",
        )
        parser.add_argument(
            "-t",
            "--timestamp",
            type=str,
            help='Reference timestamp in "YYYY-MM-DD HH:MM:SS" or ISO 8601 format.',
        )
        parser.add_argument(
            "-o",
            "--output",
            type=str,
            help="Name of the output CSV file. Defaults to 'output_YYYYMMDD_HHMMSS.csv'.",
        )
        return parser.parse_args()

    @staticmethod
    def run():
        args = CLI.parse_arguments()

        # Parse the reference timestamp if provided
        if args.timestamp:
            try:
                reference_date = FileHandler.parse_date(args.timestamp)
            except ValueError:
                print(
                    "Invalid reference timestamp format. Please use 'YYYY-MM-DD HH:MM:SS' or ISO 8601 format.",
                    file=sys.stderr,
                )
                sys.exit(1)
        else:
            reference_date = None

        # Determine the output file name
        if args.output:
            output_file = args.output
        else:
            output_file = CLI.generate_default_output_filename()

        processor = MemberProcessor(args.input, reference_date)
        try:
            members = processor.process()
            CLI.write_output(members, output_file)
        except Exception as e:
            print(f"An error occurred: {e}", file=sys.stderr)
            sys.exit(1)


# -----------------------------
# Entry Point
# -----------------------------
def main():
    CLI.run()


if __name__ == "__main__":
    main()
