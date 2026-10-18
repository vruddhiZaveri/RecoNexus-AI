CREATE ROLE reconexus_app
    NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;

GRANT CONNECT ON DATABASE reconexus TO reconexus_app;
GRANT USAGE ON SCHEMA public TO reconexus_app;

GRANT SELECT ON
    public.users,
    public.sources,
    public.batches,
    public.batch_files,
    public.transactions,
    public.audit_logs
TO reconexus_app;

GRANT INSERT ON
    public.batches,
    public.batch_files,
    public.transactions,
    public.audit_logs
TO reconexus_app;
