def complete_declaration(client):
    response = client.post(
        "/declaration/",
        data={
            "confirm_not_sensitive": True,
            "confirm_info_retained": True,
            "confirm_results_to_be_checked": True,
            "confirm_no_personal_data": True,
        },
    )
    return response
