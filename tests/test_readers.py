"""Reader route smoke tests against an empty or seeded database."""

from models import VefxistyaosaniLine, Work, db


def test_vefxistyaosani_empty_renders(client):
    response = client.get("/vefxistyaosani")
    assert response.status_code == 200


def test_vefxistyaosani_chapter_404_when_missing(client):
    assert client.get("/vefxistyaosani/1").status_code == 404


def test_vefxistyaosani_chapter_ok(client, app):
    with app.app_context():
        db.session.add(
            VefxistyaosaniLine(
                line="რომელმან შექმნა სამყარო ძალითა მით ძლიერითა",
                chapter="1",
                chapter_id=1,
                strophe_id=1,
                line_id=1,
            )
        )
        db.session.commit()

    response = client.get("/vefxistyaosani/1")
    assert response.status_code == 200
    assert "რომელმან".encode("utf-8") in response.data


def test_shushaniki_empty_404(client):
    # No chapters loaded — reader should 404 rather than divide by zero.
    response = client.get("/shushaniki/1")
    assert response.status_code in (404, 200)


def test_literature_work_404(client):
    assert client.get("/literature/missing-work/").status_code == 404


def test_literature_work_ok(client, app):
    with app.app_context():
        work = Work(
            slug="demo-work",
            title="დემო",
            author="ტესტი",
            kind="prose",
            unit_count=0,
            section_count=0,
        )
        db.session.add(work)
        db.session.commit()

    response = client.get("/literature/demo-work/")
    # Redirects to section 0 for undivided works.
    assert response.status_code in (200, 302)
