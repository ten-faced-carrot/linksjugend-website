from app import app, db, User, Aktion
from cmd import Cmd
from bcrypt import gensalt, hashpw
from getpass import getpass
import pprint
from datetime import datetime

app.app_context().push()

def parse(arg):
    return arg.split()

class Main(Cmd):
    prompt = "lj> "

    def do_db(self, args=None):
        args = parse(args)
        if args:
            if args[0] == "genall":
                db.create_all()
            
            elif args[0] == "commit":
                db.session.commit()

            elif args[0] == "info":
                print(db.session.info)
            elif args[0] == "exec":
                print(db.session.execute(input("sqlite:\\> ")))
            elif args[0] == "inspect":
                if len(args) > 1:
                    tables: list = args[1:]
                    for table in db.metadata.sorted_tables:
                        if table.name in tables:
                            tables.remove(table.name)
                            print(f'*--- {table.name} ---*')
                            print(f'| SCHEMA : {table.schema}')
                            print(f'| SPALTEN: {' '.join([i.name for i in table.columns])}')
                            print(f'*--- INFO ---*')
                            pprint.pprint(table.info)

                else:
                    md = db.metadata
                    print("Tabellen: ")
                    for table in md.sorted_tables:
                        print(f'\t* {table.name}')
                
    def do_quit(self, args=None):
        exit()

    def do_user(self, args = None):
        args = parse(args)
        if args[0]:
            if args[0] == "ls":
                for u in User.query.all():
                    u: User
                    print(u.id)
                    print(f'\t{u.name}')
                    print(f'\t{u.email}')
                    print(f'\t{u.pronouns}')
                    print(f'\t{u.rank}')
            elif args[0] == "add":
                print("Neue*n Nutzer*in erstellen")
                name = input("Name? \n")
                email = input("E-Mail? \n")
                pronouns = input("Pronomen? \n")
                password = getpass("Passwort? \n")
                password_confirm = password + "\0"
                while not password_confirm == password:
                    password_confirm = getpass("Passwort wiederholen? \n")
                rang = 10
                u = User(name = name, email = email, pronouns = pronouns, password = hashpw(password.encode(), gensalt()).decode(), rank = rang)
                db.session.add(u)
                print("User-Daten gestaged, aber noch nicht geschrieben - `db commit` zum speichern ausführen!")
    def do_aktion(self, args = None):
        args = parse(args)
        if args[0]:
            if args[0] == "ls":
                for u in Aktion.query.all():
                    u: Aktion
                    print(u._id)
                    print(f'\t{u.name}')
                    print(f'\t{u.date}')
                    print(f'\t{u.body}')
            elif args[0] == "add":
                print("Neue Aktion erstellen!")
                name = input("Name? \n")
                date_fmt = input("Datumsformat (Leerlassen für YYYY-MM-DDTHH:MM:SS)? \n") or "%Y-%m-%dT%H:%M:%S"
                date = input("Datum im o.g. Format? \n")
                date = datetime.strptime(date, date_fmt)
                body = input("Beschreibung? \n")
                u = Aktion(name = name, date = date, body = body)
                db.session.add(u)
                print(f'Um ein Bild anzuhängen, bitte eine Datei namens {u._id}.jpg in "static/aktionen" ablegen!')
                print("Daten gestaged, aber noch nicht geschrieben - `db commit` zum speichern ausführen!")
    
if __name__ == "__main__":
    Main().cmdloop()