import * as React from "react";
import Image from "next/image";

const Logo = ({ className }: { className?: string }) => (
  <Image
    src="/logo/logo1.png"
    alt="Logo"
    width={120}
    height={47}
    className={className}
    style={{ objectFit: 'contain' }}
  />
);

export default Logo;
