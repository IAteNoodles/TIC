
import { NavbarDemo } from './components/NavbarDemo'
import HeroParallaxDemo from './components/hero-parallax-demo'
import { StickyScrollRevealDemo } from './components/StickyScrollRevealDemo'
import { BackgroundGradientAnimation } from './components/ui/background-gradient-animation'

function App() {

  return (
    <BackgroundGradientAnimation>
      <div className="relative z-10">
        <NavbarDemo />
        <HeroParallaxDemo />
        <StickyScrollRevealDemo />
      </div>
    </BackgroundGradientAnimation>
  )
}

export default App
