import pytest


@pytest.mark.parametrize(
    "disabled_feature",
    [
        "accelerometer",
        "autoplay",
        "camera",
        "display-capture",
        "encrypted-media",
        "fullscreen",
        "gamepad",
        "geolocation",
        "gyroscope",
        "microphone",
        "midi",
        "payment",
    ],
)
@pytest.mark.django_db
def test_permissions_policy(client, disabled_feature):
    response = client.get("/")
    assert response.status_code == 302, response.status_code
    assert "Permissions-Policy" in response.headers, response.headers
    permissions_policy = response.headers["Permissions-Policy"]
    assert f"{disabled_feature}=()" in permissions_policy, permissions_policy


@pytest.mark.django_db
def test_csp(client):
    response = client.get("/")
    assert response.status_code == 302, response.status_code
    assert "Content-Security-Policy" in response.headers, response.headers
    csp = response.headers["Content-Security-Policy"]
    assert "unsafe" not in csp, "don't use 'unsafe-*' directives in policies"
    assert "object-src 'none'" in csp, csp
    assert "require-trusted-types-for 'script'" in csp, csp
    assert "default-src 'self'" in csp, csp
    assert "frame-ancestors 'none'" in csp, csp


@pytest.mark.django_db
def test_x_frame(client):
    response = client.get("/")
    assert response.status_code == 302, response.status_code
    x_frame = response.headers["X-Frame-Options"]
    assert "DENY" in x_frame, x_frame
