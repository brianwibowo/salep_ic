import "react";

declare module "react" {
  interface AnchorHTMLAttributes<T> extends HTMLAttributes<T> {
    referer?: string;
    referrer?: string;
  }
}

