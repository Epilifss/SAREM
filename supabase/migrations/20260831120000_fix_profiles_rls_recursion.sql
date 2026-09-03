-- Migration: Fix infinite recursion in profiles RLS policies
-- 
-- The original "Admins can view all profiles" and "Admins can manage profiles"
-- policies caused infinite recursion because they queried public.profiles
-- from within a policy ON public.profiles.
--
-- Fix: use a SECURITY DEFINER helper function that bypasses RLS when checking
-- if the current user is an admin.

-- 1. Drop the recursive policies
DROP POLICY IF EXISTS "Admins can view all profiles" ON public.profiles;
DROP POLICY IF EXISTS "Admins can manage profiles" ON public.profiles;

-- 2. Create a helper function that reads profiles WITHOUT going through RLS
--    (SECURITY DEFINER runs as the function owner, bypassing RLS)
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN AS $$
  SELECT COALESCE(
    (SELECT is_admin FROM public.profiles WHERE id = auth.uid()),
    FALSE
  );
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- 3. Recreate the policies using the helper function (no recursion)
CREATE POLICY "Admins can view all profiles"
    ON public.profiles FOR SELECT
    USING ( public.is_admin() = TRUE );

CREATE POLICY "Admins can manage profiles"
    ON public.profiles FOR ALL
    USING ( public.is_admin() = TRUE );
