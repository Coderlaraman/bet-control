declare module 'js-cookie' {
  type CookieValue = string | undefined;
  interface CookieSetOptions {
    expires?: number | Date;
    path?: string;
    domain?: string;
    secure?: boolean;
    sameSite?: 'strict' | 'lax' | 'none';
  }
  interface CookiesStatic {
    get(name: string): CookieValue;
    set(name: string, value: string, options?: CookieSetOptions): void;
    remove(name: string, options?: CookieSetOptions): void;
  }
  const Cookies: CookiesStatic;
  export default Cookies;
}