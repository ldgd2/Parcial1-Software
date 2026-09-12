import { InputWidget } from './input';
import { ButtonWidget } from './button';
import { CardWidget } from './card';
import { BadgeWidget } from './badge';
import { AnimationWidget } from './animation';
import { LayoutWidget } from './layout';
import { ShapesWidget } from './shapes';

/**
 * El objeto Widget es el punto de entrada principal ("Lego") para todos los
 * componentes de interfaz de usuario compartidos y reutilizables.
 */
export const Widget = {
  Input: InputWidget,
  Button: ButtonWidget,
  Card: CardWidget,
  Badge: BadgeWidget,
  Animation: AnimationWidget,
  Layout: LayoutWidget,
  Shapes: ShapesWidget,
};
