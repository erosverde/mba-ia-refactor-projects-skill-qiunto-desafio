import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path

from werkzeug.security import generate_password_hash

from app import create_app


class EmailRegistrationTest(unittest.TestCase):
    def setUp(self):
        folder = self.enter_temp_directory()
        self.database = str(Path(folder, "loja.db"))
        self.app = create_app({"DATABASE": self.database, "TESTING": True})
        self.client = self.app.test_client()
        self.email = "conta@example.test"

    def enter_temp_directory(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        return folder.name

    def signup(self, client, password):
        return client.post("/usuarios", json={
            "nome": "Conta de teste", "email": self.email, "senha": password,
        })

    def login(self, password):
        return self.client.post("/login", json={"email": self.email, "senha": password})

    def legacy_accounts(self, *passwords):
        ids = []
        with closing(sqlite3.connect(self.database)) as db, db:
            for password in passwords:
                cursor = db.execute(
                    "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                    ("Conta legada", self.email, generate_password_hash(password)),
                )
                ids.append(cursor.lastrowid)
        return ids

    def test_concurrent_registrations_create_one_account(self):
        passwords = ("senha-primeira", "senha-segunda")
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda pwd: self.signup(self.app.test_client(), pwd), passwords))
        self.assertCountEqual([item.status_code for item in responses], [201, 409])
        for password, response in zip(passwords, responses):
            login = self.login(password)
            if response.status_code == 201:
                self.assertEqual(login.status_code, 200)
                self.assertEqual(login.json["dados"]["id"], response.json["dados"]["id"])
            else:
                self.assertEqual(login.status_code, 401)

    def test_legacy_duplicates_keep_distinct_accounts(self):
        ids = self.legacy_accounts("senha-primeira", "senha-segunda")
        for expected_id, password in zip(ids, ("senha-primeira", "senha-segunda")):
            login = self.login(password)
            self.assertEqual(login.status_code, 200)
            self.assertEqual(login.json["dados"]["id"], expected_id)
        self.assertEqual(self.signup(self.client, "terceira-senha").status_code, 409)

    def test_ambiguous_login_requires_targeted_password_reset(self):
        first, second = self.legacy_accounts("senha-compartilhada", "senha-compartilhada")
        self.assertEqual(self.login("senha-compartilhada").status_code, 401)
        cli = self.app.test_cli_runner()
        new_password = "senha-nova"
        ambiguous = cli.invoke(args=["reset-password", self.email], input=f"{new_password}\n{new_password}\n")
        self.assertNotEqual(ambiguous.exit_code, 0)
        self.assertEqual(self.login("senha-compartilhada").status_code, 401)
        reset = cli.invoke(
            args=["reset-password", self.email, "--user-id", str(second)],
            input=f"{new_password}\n{new_password}\n",
        )
        self.assertEqual(reset.exit_code, 0, reset.output)
        self.assertEqual(self.login(new_password).json["dados"]["id"], second)
        self.assertEqual(self.login("senha-compartilhada").json["dados"]["id"], first)


if __name__ == "__main__":
    unittest.main()

