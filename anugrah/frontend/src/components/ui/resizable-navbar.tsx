"use client";
import { cn } from "@/lib/utils";
import { cva, type VariantProps } from "class-variance-authority";
import { Menu, X } from "lucide-react";
import React, { useEffect } from "react";

// Button variants
const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary: "bg-blue-600 text-white shadow hover:bg-blue-600/90",
        secondary: "bg-gray-100 text-gray-900 shadow-sm hover:bg-gray-100/80",
        outline: "border border-gray-200 bg-white shadow-sm hover:bg-gray-50 hover:text-gray-900",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
    },
  }
);

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

// Navbar Components
interface NavbarProps {
  children: React.ReactNode;
  className?: string;
}

export const Navbar: React.FC<NavbarProps> = ({ children, className }) => {
  return (
    <div className={cn("fixed top-0 inset-x-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200", className)}>
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {children}
      </div>
    </div>
  );
};

interface NavBodyProps {
  children: React.ReactNode;
  className?: string;
}

export const NavBody: React.FC<NavBodyProps> = ({ children, className }) => {
  return (
    <div className={cn("flex h-16 items-center justify-between", className)}>
      {children}
    </div>
  );
};

interface NavItem {
  name: string;
  link: string;
}

interface NavItemsProps {
  items: NavItem[];
  className?: string;
}

export const NavItems: React.FC<NavItemsProps> = ({ items, className }) => {
  return (
    <nav className={cn("hidden md:flex space-x-8", className)}>
      {items.map((item, idx) => (
        <a
          key={`nav-link-${idx}`}
          href={item.link}
          className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium transition-colors"
        >
          {item.name}
        </a>
      ))}
    </nav>
  );
};

interface NavbarLogoProps {
  className?: string;
  children?: React.ReactNode;
}

export const NavbarLogo: React.FC<NavbarLogoProps> = ({ className, children }) => {
  return (
    <div className={cn("flex items-center", className)}>
      {children || (
        <div className="text-xl font-bold text-gray-900">
          Logo
        </div>
      )}
    </div>
  );
};

export const NavbarButton: React.FC<ButtonProps> = ({ children, ...props }) => {
  return <Button {...props}>{children}</Button>;
};

// Mobile Navigation Components
interface MobileNavProps {
  children: React.ReactNode;
  className?: string;
}

export const MobileNav: React.FC<MobileNavProps> = ({ children, className }) => {
  return (
    <div className={cn("md:hidden", className)}>
      {children}
    </div>
  );
};

interface MobileNavHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export const MobileNavHeader: React.FC<MobileNavHeaderProps> = ({ children, className }) => {
  return (
    <div className={cn("flex h-16 items-center justify-between px-4", className)}>
      {children}
    </div>
  );
};

interface MobileNavToggleProps {
  isOpen: boolean;
  onClick: () => void;
  className?: string;
}

export const MobileNavToggle: React.FC<MobileNavToggleProps> = ({ isOpen, onClick, className }) => {
  return (
    <button
      onClick={onClick}
      className={cn("p-2 text-gray-600 hover:text-gray-900 transition-colors", className)}
      aria-label="Toggle menu"
    >
      {isOpen ? <X size={24} /> : <Menu size={24} />}
    </button>
  );
};

interface MobileNavMenuProps {
  children: React.ReactNode;
  isOpen: boolean;
  onClose: () => void;
  className?: string;
}

export const MobileNavMenu: React.FC<MobileNavMenuProps> = ({ 
  children, 
  isOpen, 
  className 
}) => {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 top-16 z-40 bg-white">
      <div className={cn("flex flex-col space-y-4 p-6", className)}>
        {children}
      </div>
    </div>
  );
};