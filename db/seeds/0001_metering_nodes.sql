INSERT INTO metering_node (id, code, name, line_name) VALUES
    ('11111111-1111-1111-1111-111111111111', 'PIRG-01', 'Metering node 1', 'Line A'),
    ('22222222-2222-2222-2222-222222222222', 'PIRG-02', 'Metering node 2', 'Line A'),
    ('33333333-3333-3333-3333-333333333333', 'PIRG-03', 'Metering node 3', 'Line B')
ON CONFLICT (code) DO NOTHING;