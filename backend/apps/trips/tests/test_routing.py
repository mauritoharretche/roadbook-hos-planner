from apps.trips.routing import MockRoutingProvider


def test_mock_geocoding_is_deterministic_for_known_location():
    provider = MockRoutingProvider()

    first = provider.geocode("La Plata, Buenos Aires, Argentina")
    second = provider.geocode("  la plata, buenos aires, argentina  ")

    assert first.latitude == -34.9214
    assert first.longitude == -57.9544
    assert second.latitude == first.latitude
    assert second.longitude == first.longitude


def test_mock_geocoding_fallback_is_deterministic():
    provider = MockRoutingProvider()

    assert provider.geocode("Assessment depot").latitude == provider.geocode(
        "assessment depot"
    ).latitude
    assert provider.geocode("Assessment depot").longitude == provider.geocode(
        "assessment depot"
    ).longitude


def test_mock_route_is_deterministic_and_ordered():
    provider = MockRoutingProvider()
    locations = [
        provider.geocode("La Plata, Buenos Aires, Argentina"),
        provider.geocode("Buenos Aires, Argentina"),
        provider.geocode("Rosario, Santa Fe, Argentina"),
    ]

    first = provider.calculate_route(locations)
    second = provider.calculate_route(locations)

    assert first == second
    assert len(first.legs) == 2
    assert first.distance_miles > 0
    assert first.duration_minutes > 0
    assert first.geometry[0] == (locations[0].longitude, locations[0].latitude)
    assert first.geometry[-1] == (locations[-1].longitude, locations[-1].latitude)
