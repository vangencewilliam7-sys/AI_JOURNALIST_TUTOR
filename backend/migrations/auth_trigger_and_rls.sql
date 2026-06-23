-- Trigger to automatically create an 'experts' row when a new user signs up in Supabase Auth
CREATE OR REPLACE FUNCTION public.handle_new_user() 
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.experts (id, name, domain, stream_type)
  VALUES (
    new.id, 
    COALESCE(new.raw_user_meta_data->>'name', 'Expert ' || split_part(new.email, '@', 1)),
    COALESCE(new.raw_user_meta_data->>'domain', 'General'),
    COALESCE(new.raw_user_meta_data->>'stream_type', 'general')
  );
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- Enable RLS and create policies for `experts`
ALTER TABLE public.experts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own expert profile" ON public.experts;
CREATE POLICY "Users can view own expert profile" ON public.experts
  FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own expert profile" ON public.experts;
CREATE POLICY "Users can update own expert profile" ON public.experts
  FOR UPDATE USING (auth.uid() = id);

-- Enable RLS and create policies for `interview_sessions`
ALTER TABLE public.interview_sessions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own sessions" ON public.interview_sessions;
CREATE POLICY "Users can view own sessions" ON public.interview_sessions
  FOR SELECT USING (auth.uid() = expert_id);

DROP POLICY IF EXISTS "Users can insert own sessions" ON public.interview_sessions;
CREATE POLICY "Users can insert own sessions" ON public.interview_sessions
  FOR INSERT WITH CHECK (auth.uid() = expert_id);

DROP POLICY IF EXISTS "Users can update own sessions" ON public.interview_sessions;
CREATE POLICY "Users can update own sessions" ON public.interview_sessions
  FOR UPDATE USING (auth.uid() = expert_id);
