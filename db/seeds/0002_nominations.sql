INSERT INTO delivery_point (id, code, name, counterparty_name, notify_channel, notify_address) VALUES
    ('aaaaaaaa-0000-0000-0000-000000000001', 'DP-01', 'Delivery point 1', 'Counterparty A', 'email', 'ops@counterparty-a.example'),
    ('aaaaaaaa-0000-0000-0000-000000000002', 'DP-02', 'Delivery point 2', 'Counterparty B', 'email', 'ops@counterparty-b.example')
ON CONFLICT (code) DO NOTHING;

INSERT INTO node_delivery_link (node_id, delivery_point_id) VALUES
    ('11111111-1111-1111-1111-111111111111', 'aaaaaaaa-0000-0000-0000-000000000001'),
    ('22222222-2222-2222-2222-222222222222', 'aaaaaaaa-0000-0000-0000-000000000001'),
    ('33333333-3333-3333-3333-333333333333', 'aaaaaaaa-0000-0000-0000-000000000002')
ON CONFLICT DO NOTHING;

INSERT INTO nomination (id, delivery_point_id, gas_day, planned_volume, threshold_pct) VALUES
    ('bbbbbbbb-0000-0000-0000-000000000001', 'aaaaaaaa-0000-0000-0000-000000000001', '2026-09-10', 1200.000, 5.00),
    ('bbbbbbbb-0000-0000-0000-000000000002', 'aaaaaaaa-0000-0000-0000-000000000002', '2026-09-10', 900.000, 3.00)
ON CONFLICT (delivery_point_id, gas_day) DO NOTHING;