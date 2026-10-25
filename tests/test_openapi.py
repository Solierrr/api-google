from app.main import app
from app.openapi import build_openapi


def test_public_contract_hides_internal_routes_and_empty_tags():
    contract = app.openapi()

    assert contract["info"]["title"] == "Solaria — api-google"
    assert contract["servers"][0]["description"] == "QA"
    assert not [path for path in contract["paths"] if path.startswith("/internal/")]
    assert {tag["name"] for tag in contract["tags"]} == {"Endereços", "Geografia", "Saúde"}
    assert contract["security"] == [{"bearerAuth": []}]


def test_exported_contract_documents_internal_routes_with_service_key():
    contract = build_openapi(app, include_internal=True)

    translate = contract["paths"]["/internal/i18n/translate"]["post"]
    assert translate["security"] == [{"serviceKey": []}]
    assert translate["x-error-codes"] == [
        "UNAUTHENTICATED",
        "FORBIDDEN",
        "VALIDATION_FAILED",
        "MALFORMED_REQUEST",
        "DEPENDENCY_UNAVAILABLE",
        "INTERNAL_ERROR",
    ]
    assert contract["components"]["securitySchemes"]["serviceKey"] == {
        "type": "apiKey",
        "in": "header",
        "name": "X-Service-Key",
    }


def test_every_error_response_uses_problem_detail():
    contract = build_openapi(app, include_internal=True)

    for path in contract["paths"].values():
        for operation in path.values():
            assert "500" in operation["responses"]
            for status, response in operation["responses"].items():
                if status.startswith(("4", "5")):
                    schema = response["content"]["application/problem+json"]["schema"]
                    assert schema == {"$ref": "#/components/schemas/ProblemDetail"}
    assert "HTTPValidationError" not in contract["components"]["schemas"]


def test_health_routes_are_public():
    contract = app.openapi()

    assert contract["paths"]["/health"]["get"]["security"] == []
    assert contract["paths"]["/ready"]["get"]["security"] == []


def test_legacy_routes_stay_out_of_the_contract():
    contract = build_openapi(app, include_internal=True)

    assert "/v1/i18n/translate" not in contract["paths"]
    assert "/v1/solar/roof-viability" not in contract["paths"]
