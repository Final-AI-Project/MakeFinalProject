// hooks/useAuthGuard.ts
import { useEffect } from "react";
import { useRouter, usePathname } from "expo-router";
import { getToken } from "../libs/auth";

/**
 * 인증이 필요한 페이지에서 토큰을 확인하고,
 * 토큰이 없으면 로그인 페이지로 리다이렉트하는 훅
 */
export function useAuthGuard() {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const checkAuth = async () => {
      // 로그인/회원가입 페이지는 인증 체크 제외
      const publicRoutes = ["/(auth)/login", "/(auth)/signup"];
      const isPublicRoute = publicRoutes.some((route) =>
        pathname?.startsWith(route)
      );

      if (isPublicRoute) {
        return; // 공개 페이지는 인증 체크하지 않음
      }

      try {
        const token = await getToken();

        // 토큰이 없으면 로그인 페이지로 리다이렉트
        if (!token) {
          console.log("No token found, redirecting to login");
          router.replace("/(auth)/login" as any);
        }
      } catch (error) {
        console.error("Auth check failed:", error);
        // 에러 발생 시에도 로그인 페이지로 리다이렉트
        router.replace("/(auth)/login" as any);
      }
    };

    checkAuth();
  }, [pathname, router]);
}
