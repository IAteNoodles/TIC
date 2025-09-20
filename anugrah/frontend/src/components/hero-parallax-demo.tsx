import { HeroParallax } from "@/components/ui/hero-parallax";
import { products } from "@/lib/products";

export default function HeroParallaxDemo() {
  return <HeroParallax products={products} />;
}