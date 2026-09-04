CREATE TABLE public.application_error_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    source VARCHAR(120) NOT NULL,
    message TEXT NOT NULL,
    details TEXT,
    stack TEXT,
    path VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.application_error_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can create application error logs"
    ON public.application_error_logs FOR INSERT
    WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Admins can view application error logs"
    ON public.application_error_logs FOR SELECT
    USING ((SELECT is_admin FROM public.profiles WHERE id = auth.uid()) = TRUE);