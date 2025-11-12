import textwrap


def test_list_csvs_includes_example(client):
    response = client.get("/csvs")
    assert response.status_code == 200
    assert "example_basic.csv" in response.json()["files"]


def test_upload_fetch_delete_csv(client):
    content = textwrap.dedent(
        """\
        Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well
        tube_rack_96_1500ul_4,A1,10,384_ppv_55ul_2,A1
        """
    )
    upload_response = client.post(
        "/csvs",
        json={"name": "custom.csv", "content": content},
    )
    assert upload_response.status_code == 201
    assert upload_response.json()["name"] == "custom.csv"

    fetch_response = client.get("/csvs/custom.csv")
    assert fetch_response.status_code == 200
    assert "tube_rack_96_1500ul_4" in fetch_response.text

    delete_response = client.delete("/csvs/custom.csv")
    assert delete_response.status_code == 204

    missing_response = client.get("/csvs/custom.csv")
    assert missing_response.status_code == 404
