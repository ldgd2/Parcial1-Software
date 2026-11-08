import 'package:flutter/material.dart';
import '../../../../shared/utils/ui_engine/ui_screen.dart';
import '../../../../shared/utils/ui_engine/widget_modifiers.dart';
import '../../../../shared/utils/ui_engine/list_modifiers.dart';
import '../../../../shared/utils/ui_engine/string_modifiers.dart';
import '../../../../shared/utils/ui_engine/icon_modifiers.dart';
import '../../../../shared/utils/ui_engine/tema.dart';

import '../../../../core/network/api_provider.dart';

// Inputs
import '../../../../shared/widgets/inputs/custom_input.dart';
import '../../../../shared/widgets/inputs/custom_input_form.dart';
import '../../../../shared/widgets/inputs/custom_input_search.dart';
import '../../../../shared/widgets/inputs/custom_input_otp.dart';
import '../../../../shared/widgets/inputs/custom_input_phone.dart';
import '../../../../shared/widgets/inputs/custom_input_currency.dart';
import '../../../../shared/widgets/inputs/custom_input_textarea.dart';
import '../../../../shared/widgets/inputs/custom_input_password.dart';
import '../../../../shared/widgets/inputs/custom_input_password_create.dart';
import '../../../../shared/widgets/inputs/custom_input_email.dart';
import '../../../../shared/widgets/inputs/custom_input_number.dart';
import '../../../../shared/widgets/inputs/custom_input_dropdown.dart';
import '../../../../shared/widgets/inputs/custom_input_date.dart';

// Pickers
import '../../../../shared/widgets/pickers/custom_date_picker.dart';
import '../../../../shared/widgets/pickers/custom_time_picker.dart';
import '../../../../shared/widgets/pickers/custom_date_range_picker.dart';
import '../../../../shared/widgets/pickers/custom_bottom_sheet_picker.dart';

// Switches
import '../../../../shared/widgets/switches/custom_switch.dart';
import '../../../../shared/widgets/switches/custom_switch_tile.dart';
import '../../../../shared/widgets/switches/custom_switch_card.dart';
import '../../../../shared/widgets/switches/custom_switch_icon.dart';
import '../../../../shared/widgets/switches/custom_switch_async.dart';

// Sliders
import '../../../../shared/widgets/sliders/custom_slider.dart';
import '../../../../shared/widgets/sliders/custom_range_slider.dart';
import '../../../../shared/widgets/sliders/custom_slider_icon.dart';
import '../../../../shared/widgets/sliders/custom_slider_discrete.dart';
import '../../../../shared/widgets/sliders/custom_slider_card.dart';

// Cards
import '../../../../shared/widgets/cards/custom_card_info.dart';
import '../../../../shared/widgets/cards/custom_card_product.dart';
import '../../../../shared/widgets/cards/custom_card_stat.dart';
import '../../../../shared/widgets/cards/custom_card_profile.dart';
import '../../../../shared/widgets/cards/custom_card_banner.dart';
import '../../../../shared/widgets/cards/custom_card_media.dart';
import '../../../../shared/widgets/cards/custom_card_action.dart';

// Buttons
import '../../../../shared/widgets/buttons/custom_button_primary.dart';
import '../../../../shared/widgets/buttons/custom_button_secondary.dart';
import '../../../../shared/widgets/buttons/custom_button_outline.dart';
import '../../../../shared/widgets/buttons/custom_button_text.dart';
import '../../../../shared/widgets/buttons/custom_button_danger.dart';
import '../../../../shared/widgets/buttons/custom_button_icon.dart';

// Dialogs
import '../../../../shared/widgets/dialogs/custom_dialog_confirmation.dart';
import '../../../../shared/widgets/dialogs/custom_dialog_danger.dart';
import '../../../../shared/widgets/dialogs/custom_dialog_success.dart';
import '../../../../shared/widgets/dialogs/custom_dialog_warning.dart';
import '../../../../shared/widgets/dialogs/custom_dialog_input.dart';
import '../../../../shared/widgets/dialogs/custom_dialog_loading.dart';
import '../../../../shared/widgets/dialogs/custom_dialog_info.dart';

// Dismissible (Swipe-to-Dismiss)
import '../../../../shared/widgets/dismissible/custom_dismissible_card.dart';

// Grids (Cuadrículas y Matrices)
import '../../../../shared/widgets/grids/custom_grid_stats.dart';
import '../../../../shared/widgets/grids/custom_grid_matrix.dart';
import '../../../../shared/widgets/grids/custom_grid_media.dart';
import '../../../../shared/widgets/grids/custom_grid_product.dart';

import '../../../../shared/widgets/avatars/custom_avatar.dart';
import '../../../../shared/widgets/viewers/custom_interactive_viewer.dart';
import '../../../../shared/widgets/pickers/custom_media_picker.dart';

// Speed Dial (Marcación Rápida / Expandable FAB)
import '../../../../shared/widgets/speed_dial/custom_smart_speed_dial.dart';
import '../../../../shared/widgets/speed_dial/custom_speed_dial_item.dart';

// Navigation Bars (AppBars y Bottom App Bars con Notch)
import '../../../../shared/widgets/bars/custom_bottom_app_bar.dart';
import '../../../../shared/widgets/bars/custom_bottom_app_bar_item.dart';

// Loaders y Esqueletos
import '../../../../shared/widgets/loaders/custom_skeleton.dart';
import '../../../../shared/widgets/loaders/custom_loader_dots.dart';
import '../../../../shared/widgets/loaders/custom_loader_linear.dart';
import '../../../../shared/widgets/loaders/custom_spinner.dart';
import '../../../../shared/widgets/loaders/custom_loader_typing.dart';
import '../../../../shared/widgets/loaders/custom_loader_wave.dart';
import '../../../../shared/widgets/loaders/custom_loader_pulse.dart';
import '../../../../shared/widgets/loaders/custom_loader_overlay.dart';

// Animaciones
import 'package:flutter_animate/flutter_animate.dart';
import '../../../../shared/animation/custom_animation.dart';

class Suma {
  int num1 = 0;
  
   void sumar(){
    num1++;
  }
  
  int mostrar(){
    return num1;
  }
}

class PantallaAux extends UIScreen {
  static final Suma n = Suma();

  PantallaAux({super.key}) : super(
    titulo: "pantallaAux",
    centrado: true,
    paddingX: 20.0,
    paddingY: 12.0,
    accionesAppBar: [
      Icons.notifications_outlined.icono(size: 26).padSolo(r: 15).click(() {}),
    ],
    // Definición de la interfaz mediante inyección directa
    cuerpo: (context) => [
      "holaMundo".texto(color: Colors.blue, negrita: true),
      
      // Componente reactivo aislado
      CustomRebuilder(
        builder: (actualizar) => [
          CustomPrimaryButton(
            text: "Sumar",  
            backgroundColor: Colors.red, 
            onPressed: () => actualizar(() => n.sumar()),
          ),
          if(n.mostrar() == 6 || n.mostrar() == 7 || n.mostrar() == 67) 
            "Six seven".texto(color: Colors.blue, size: 24, negrita: true),
          n.mostrar().toString().texto(color: Colors.red, size: 24, negrita: true),
        ].columna(espaciado: 10),
      ),
    ],
  );
}