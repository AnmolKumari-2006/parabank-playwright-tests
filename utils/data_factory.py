"""Creates fake but valid test data with Faker.

Every call returns a new unique user, so no test depends on data
created by another test or by an earlier run.
"""
import uuid
from dataclasses import dataclass, asdict
from faker import Faker

fake = Faker("en_US")  # ParaBank follows US formats (ZIP, SSN, phone)


@dataclass
class User:
    first_name: str
    last_name: str
    street: str
    city: str
    state: str
    zip_code: str
    phone: str
    ssn: str
    username: str
    password: str

    def as_dict(self) -> dict:
        return asdict(self)


def unique_username() -> str:
    # 'pb' + 10 random hex characters; uuid makes a clash practically impossible
    return "pb" + uuid.uuid4().hex[:10]


def new_user() -> User:
    return User(
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        street=fake.street_address(),
        city=fake.city(),
        state=fake.state_abbr(),
        zip_code=fake.numerify("#####"),
        phone=fake.numerify("##########"),
        ssn=fake.numerify("###-##-####"),
        username=unique_username(),
        password="Pw" + uuid.uuid4().hex[:8] + "!",
    )
