import React from 'react';
import { Widget } from '../../../shared/components/ui/Widget';
import { HeroSection } from './HeroSection';
import { FeaturesSection } from './FeaturesSection';
import { PricingSection } from './PricingSection';
import { InteractiveBackground } from './InteractiveBackground';
import './landing.css';

export const LandingView: React.FC = () => {
  return (
    <div className="landing-layout">
      <InteractiveBackground />
      <Widget.Layout.Navbar />
      
      <main className="landing-main" style={{ position: 'relative', zIndex: 1 }}>
        <HeroSection />
        <FeaturesSection />
        <PricingSection />
      </main>
      
      <Widget.Layout.Footer />
    </div>
  );
};
