from datetime import date


def test_register_login_and_me(client):
    payload = {
        "name": "João Silva",
            "email": "joao@empresa.example.com",
        "password": "senha1234",
        "company_name": "Silva Studio",
    }
    created = client.post("/api/v1/auth/register", json=payload)
    assert created.status_code == 201
    token = created.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "joao@empresa.example.com"
    assert me.json()["company"]["name"] == "Silva Studio"

    login = client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert login.status_code == 200

    failed = client.post("/api/v1/auth/login", json={"email": payload["email"], "password": "erradaaaa"})
    assert failed.status_code == 400


def test_protected_without_token(client):
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 401


def test_transaction_crud_and_filters(auth_client):
    client, headers = auth_client
    categories = client.get("/api/v1/categories", headers=headers).json()
    sales = next(item for item in categories if item["name"] == "Vendas")
    suppliers = next(item for item in categories if item["name"] == "Fornecedores")

    income = client.post(
        "/api/v1/transactions",
        headers=headers,
        json={
            "date": "2026-09-01",
            "description": "Venda #1001",
            "type": "income",
            "category_id": sales["id"],
            "amount": 850,
            "status": "paid",
        },
    )
    assert income.status_code == 201, income.text

    expense = client.post(
        "/api/v1/transactions",
        headers=headers,
        json={
            "date": "2026-09-02",
            "description": "Pagamento fornecedor",
            "type": "expense",
            "category_id": suppliers["id"],
            "amount": 200,
            "status": "paid",
        },
    )
    assert expense.status_code == 201

    pending = client.post(
        "/api/v1/transactions",
        headers=headers,
        json={
            "date": "2026-09-03",
            "description": "Conta de energia",
            "type": "expense",
            "category_id": suppliers["id"],
            "amount": 430,
            "status": "pending",
            "due_date": "2026-09-10",
            "party_name": "Concessionária",
        },
    )
    assert pending.status_code == 201
    pending_id = pending.json()["id"]

    listed = client.get("/api/v1/transactions?search=fornecedor", headers=headers)
    assert listed.json()["total"] == 1

    by_type = client.get("/api/v1/transactions?type=income", headers=headers)
    assert by_type.json()["total"] == 1

    settled = client.post(f"/api/v1/transactions/{pending_id}/settle", headers=headers)
    assert settled.status_code == 200
    assert settled.json()["status"] == "paid"

    dashboard = client.get("/api/v1/dashboard?period=custom&date_from=2026-09-01&date_to=2026-09-30", headers=headers)
    body = dashboard.json()
    assert dashboard.status_code == 200
    assert body["total_income"] == 850
    assert body["total_expense"] == 630
    assert body["profit"] == 220


def test_tenant_isolation(client):
    first = client.post(
        "/api/v1/auth/register",
        json={
            "name": "User A",
                "email": "a@iso.example.com",
            "password": "senha1234",
            "company_name": "Empresa A",
        },
    ).json()
    second = client.post(
        "/api/v1/auth/register",
        json={
            "name": "User B",
                "email": "b@iso.example.com",
            "password": "senha1234",
            "company_name": "Empresa B",
        },
    ).json()
    headers_a = {"Authorization": f"Bearer {first['access_token']}"}
    headers_b = {"Authorization": f"Bearer {second['access_token']}"}
    categories = client.get("/api/v1/categories", headers=headers_a).json()
    sales = next(item for item in categories if item["name"] == "Vendas")
    created = client.post(
        "/api/v1/transactions",
        headers=headers_a,
        json={
            "date": "2026-09-01",
            "description": "Somente A",
            "type": "income",
            "category_id": sales["id"],
            "amount": 999,
            "status": "paid",
        },
    )
    tx_id = created.json()["id"]
    listed_b = client.get("/api/v1/transactions", headers=headers_b)
    assert listed_b.json()["total"] == 0
    forbidden = client.get(f"/api/v1/transactions/{tx_id}", headers=headers_b)
    assert forbidden.status_code == 404


def test_csv_import_confirm(auth_client):
    client, headers = auth_client
    content = (
        "data,descricao,categoria,tipo,valor,status\n"
        "01/09/2026,Pagamento fornecedor,Fornecedores,despesa,1200,pago\n"
        "02/09/2026,Venda #1023,Vendas,receita,850,pago\n"
        "03/09/2026,Linha ruim,Operacional,despesa,abc,pago\n"
    )
    files = {"file": ("mov.csv", content, "text/csv")}
    preview = client.post("/api/v1/imports/preview", headers=headers, files=files)
    assert preview.status_code == 200
    assert preview.json()["valid_count"] == 2
    assert preview.json()["error_count"] == 1

    files = {"file": ("mov.csv", content, "text/csv")}
    confirm = client.post("/api/v1/imports/confirm", headers=headers, files=files)
    assert confirm.status_code == 200
    assert confirm.json()["imported_count"] == 2
    listed = client.get("/api/v1/transactions", headers=headers)
    assert listed.json()["total"] == 2


def test_category_delete_blocked_when_used(auth_client):
    client, headers = auth_client
    created = client.post(
        "/api/v1/categories",
        headers=headers,
        json={"name": "Eventos", "type": "expense"},
    )
    category_id = created.json()["id"]
    client.post(
        "/api/v1/transactions",
        headers=headers,
        json={
            "date": "2026-09-01",
            "description": "Stand",
            "type": "expense",
            "category_id": category_id,
            "amount": 50,
            "status": "paid",
        },
    )
    deleted = client.delete(f"/api/v1/categories/{category_id}", headers=headers)
    assert deleted.status_code == 400
