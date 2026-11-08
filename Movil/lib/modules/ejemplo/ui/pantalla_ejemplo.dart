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

/// Pantalla de Demostración del Sistema de Diseño y Arquitectura Modular.
/// Construida de forma puramente declarativa utilizando únicamente abstracciones de alto nivel.
class PantallaEjemplo extends UIScreen {
  PantallaEjemplo({super.key})
      : super(
          titulo: "carambaaaaaaax",
          centrado: true,
          paddingX: 50.0,
          paddingY: 12.0,
          accionesAppBar: [
            Icons.notifications_outlined.icono(size: 26).padSolo(r: 15).click(() {}),
          ],
          posicionBotonFlotante: PosicionBotonFlotante.centro,
          botonFlotante: CustomSmartSpeedDial(
            items: [
              CustomSpeedDialItem(
                label: "Nuevo Proyecto",
                icon: Icons.create_new_folder_outlined,
                onPressed: () {},
              ),
              CustomSpeedDialItem(
                label: "Escanear Documento",
                icon: Icons.document_scanner_outlined,
                onPressed: () {},
              ),
              CustomSpeedDialItem(
                label: "Nuevo Contacto",
                icon: Icons.person_add_alt_1_outlined,
                onPressed: () {},
              ),
              CustomSpeedDialItem(
                label: "Registrar Pago",
                icon: Icons.attach_money_rounded,
                onPressed: () {},
              ),
            ],
          ),
          bottomNavigationBar: CustomBottomAppBar(
            currentIndex: 0,
            items: const [
              CustomBottomNavItem(
                label: "Inicio",
                icon: Icons.home_outlined,
                activeIcon: Icons.home_rounded,
              ),
              CustomBottomNavItem(
                label: "Billetera",
                icon: Icons.account_balance_wallet_outlined,
                activeIcon: Icons.account_balance_wallet_rounded,
                badgeCount: 3,
              ),
              CustomBottomNavItem(
                label: "Mensajes",
                icon: Icons.chat_bubble_outline_rounded,
                activeIcon: Icons.chat_bubble_rounded,
                badgeCount: 1,
              ),
              CustomBottomNavItem(
                label: "Perfil",
                icon: Icons.person_outline_rounded,
                activeIcon: Icons.person_rounded,
              ),
            ],
          ),
        );

  @override
  Widget contenido(BuildContext context) {
    final colores = context.colores;
    final textos = context.textos;

    return <Widget>[
      // 1. CABECERA Y AVATAR CON BADGE DE ESTADO
      [
        Icons.person.icono(size: 70, color: colores.fondoSecundario)
            .pad(18)
            .fondo(colores.primario)
            .clip(radio: 40)
            .sombra(color: colores.primario.withValues(alpha: 0.35), difuminado: 12),

        const SizedBox(width: 18, height: 18)
            .estilo(bg: colores.exito, circulo: true, bordeColor: colores.fondoSecundario, bordeGrosor: 3)
            .pos(x: 26, y: 26),
      ].apilar(alineacion: Alignment.center).padXY(0, 10),

      "Ana Desarrolladora".texto(
        size: textos.titulo.fontSize!,
        negrita: true,
        color: colores.textoPrincipal,
        alineacion: TextAlign.center,
      ),

      "Arquitectura Limpia & UI Engine"
          .texto(size: textos.cuerpo.fontSize!, color: colores.primario, alineacion: TextAlign.center, cursiva: true)
          .padXY(0, 4),

      const _SimpsonsApiDemo(),

      // 2. MÉTRICAS CON TARJETAS REUTILIZABLES (CustomStatCard)
      [
        const CustomStatCard(title: "Proyectos", value: "42", icon: Icons.folder_open, subtitle: "Completados").w(115),
        const CustomStatCard(title: "Seguidores", value: "12.4K", icon: Icons.people_outline, trendText: "+14%").w(125),
        const CustomStatCard(title: "Rating", value: "4.9", icon: Icons.star_border, subtitle: "Excelente").w(115),
      ].envoltura(espaciado: 12).padXY(0, 20),

      // 3. TARJETAS ESPECIALIZADAS (CARDS SUITE)
      "Tarjetas Especializadas (Cards)".texto(size: textos.subtitulo.fontSize!, color: colores.textoPrincipal, negrita: true).padSolo(b: 10),

      // Tarjeta Informativa Base (CustomInfoCard)
      const CustomInfoCard(
        title: "Arquitectura 100% Abstracta",
        description: "Cada componente encapsula su diseño sin requerir contenedores o layouts manuales.",
        icon: Icons.auto_awesome,
      ).maxAncho(400).padXY(0, 6),

      // Banner Promocional con Gradiente (CustomBannerCard)
      CustomBannerCard(
        title: "¡Desbloquea Plan Pro!",
        subtitle: "Acceso ilimitado a todas las herramientas avanzadas y reportes.",
        buttonText: "Mejorar Ahora",
        icon: Icons.workspace_premium_outlined,
        onButtonPressed: () {},
      ).maxAncho(400).padXY(0, 6),

      // Tarjeta de Perfil Profesional (CustomProfileCard)
      CustomProfileCard(
        name: "Elena Rostova",
        role: "Senior UI/UX Designer",
        company: "Design Systems",
        isOnline: true,
        bio: "Especialista en interfaces móviles limpias, interacciones táctiles y accesibilidad.",
        tags: const ["Figma", "Flutter", "Clean Code"],
        actionButton: IconButton(
          icon: Icon(Icons.more_vert, color: colores.textoSecundario),
          onPressed: () {},
        ),
      ).maxAncho(400).padXY(0, 6),

      // Tarjeta de Producto (CustomProductCard)
      CustomProductCard(
        title: "Auriculares Inalámbricos Noise Cancelling Pro",
        price: "\$89.99",
        originalPrice: "\$129.99",
        category: "Audio & Sonido",
        rating: 4.8,
        reviewsCount: 142,
        badgeText: "30% OFF",
        isFavorite: true,
        width: 320,
        onAddToCart: () {},
      ).padXY(0, 6),

      // Tarjeta de Contenido / Artículo (CustomMediaCard)
      CustomMediaCard(
        title: "Buenas prácticas en arquitectura modular para Flutter",
        snippet: "Aprende cómo organizar tus capas compartidas y módulos para escalar tu equipo.",
        category: "ARQUITECTURA",
        date: "Hoy",
        readTime: "4 min lectura",
        isBookmarked: true,
        onBookmark: () {},
      ).maxAncho(400).padXY(0, 6),

      // Tarjetas de Selección / Métodos de Pago (CustomActionCard)
      CustomActionCard(
        title: "Tarjeta Visa terminada en 4821",
        subtitle: "Vence 08/28 • Tarjeta principal",
        icon: Icons.credit_card,
        isSelected: true,
        onTap: () {},
      ).maxAncho(400).padXY(0, 4),

      CustomActionCard(
        title: "PayPal Express Checkout",
        subtitle: "usuario@ejemplo.com",
        icon: Icons.account_balance_wallet_outlined,
        showChevron: true,
        onTap: () {},
      ).maxAncho(400).padXY(0, 16),

      // 4. FORMULARIO E INPUTS (INPUTS SUITE)
      "Entradas de Texto (Inputs)".texto(size: textos.subtitulo.fontSize!, color: colores.textoPrincipal, negrita: true).padSolo(b: 10),

      // 1. Barra de Búsqueda
      CustomSearchInput(
        hint: "Buscar en la aplicación...",
        fillColor: colores.fondoSecundario,
        onChanged: (val) {},
      ).maxAncho(400).padXY(0, 6),

      // 2. Campo de Texto Estándar (CustomInput)
      const CustomInput(
        label: "Nombre Completo",
        hint: "Ej. Ana Pérez",
        prefixIcon: Icons.person_outline,
      ).maxAncho(400).padXY(0, 6),

      // 3. Campo de Correo Electrónico con teclado @
      const CustomEmailInput(
        label: "Correo Electrónico",
        hint: "usuario@empresa.com",
      ).maxAncho(400).padXY(0, 6),

      // 3. Contraseña Estándar (Login)
      const CustomPasswordInput(
        label: "Contraseña de Acceso",
        hint: "Ingresa tu contraseña",
      ).maxAncho(400).padXY(0, 6),

      // 4. Creador de Contraseñas con Checklist de Complejidad
      const CustomPasswordCreateInput(
        label: "Crear Nueva Contraseña (Registro)",
        hint: "Mín. 8 caracteres, mayús, núm, símbolo",
        showChecklist: true,
        showStrengthBar: true,
        showPoints: true,
      ).maxAncho(400).padXY(0, 6),

      // 5. Teléfono Internacional y Monto en Moneda (Fila)
      [
        const CustomPhoneInput(
          label: "Teléfono Móvil",
          hint: "412 123 4567",
        ).expandir(),

        const CustomCurrencyInput(
          label: "Presupuesto",
          hint: "500.00",
          currencySymbol: "\$",
        ).expandir(),
      ].fila(espaciado: 12, mainAxisSize: MainAxisSize.max).maxAncho(400).padXY(0, 6),

      // 5. Código de Verificación OTP (6 casillas con auto-avance)
      "Código de Verificación (OTP 6 dígitos)"
          .texto(size: textos.cuerpoPequeno.fontSize!, color: colores.textoPrincipal, negrita: true)
          .padSolo(t: 6, b: 6),
      const CustomOtpInput(
        length: 6,
        autofocus: false,
      ).maxAncho(400).padXY(0, 8),

      // 6. Campo con Validación Obligatoria (Text Form Field)
      const CustomFormFieldInput(
        label: "Nombre de Usuario (Obligatorio)",
        hint: "Ej. anaperez_dev",
        prefixIcon: Icons.alternate_email,
        isRequired: true,
        minLength: 4,
      ).maxAncho(400).padXY(0, 6),

      // 7. Área de Texto Multilínea con Contador
      const CustomTextAreaInput(
        label: "Biografía Profesional",
        hint: "Escribe sobre tu experiencia, proyectos y metas...",
        minLines: 3,
        maxLines: 5,
        maxLength: 250,
      ).maxAncho(400).padXY(0, 6),

      // 8. Fila con Edad y Fecha
      [
        CustomNumberInput(
          label: "Edad",
          hint: "Ej. 28",
          fillColor: colores.fondoSecundario,
        ).expandir(),

        CustomDateInput(
          label: "Nacimiento",
          hint: "Seleccionar",
          fillColor: colores.fondoSecundario,
        ).expandir(),
      ].fila(espaciado: 12, mainAxisSize: MainAxisSize.max).maxAncho(400).padXY(0, 6),

      CustomDropdownInput<String>(
        label: "Rol en la empresa",
        hint: "Selecciona un rol",
        fillColor: colores.fondoSecundario,
        prefixIcon: Icons.work_outline,
        options: const {
          "dev": "Desarrollador",
          "design": "Diseñador",
          "pm": "Product Manager",
        },
        onChanged: (val) {},
      ).maxAncho(400).padXY(0, 16),

      // 5. SELECTORES TÁCTILES (PICKERS SUITE)
      "Selectores Táctiles (Pickers)".texto(size: textos.subtitulo.fontSize!, color: colores.textoPrincipal, negrita: true).padSolo(b: 10),

      [
        CustomDatePicker(
          label: "Fecha (Calendario)",
          hint: "Seleccionar",
          fillColor: colores.fondoSecundario,
          style: DatePickerStyle.material,
        ).expandir(),

        CustomDatePicker(
          label: "Fecha (Rueda iOS)",
          hint: "Seleccionar",
          fillColor: colores.fondoSecundario,
          style: DatePickerStyle.cupertinoWheel,
        ).expandir(),
      ].fila(espaciado: 12, mainAxisSize: MainAxisSize.max).maxAncho(400).padXY(0, 6),

      [
        CustomTimePicker(
          label: "Hora de entrada",
          hint: "Seleccionar",
          fillColor: colores.fondoSecundario,
          style: TimePickerStyle.materialClock,
        ).expandir(),

        CustomTimePicker(
          label: "Hora de salida (iOS)",
          hint: "Seleccionar",
          fillColor: colores.fondoSecundario,
          style: TimePickerStyle.cupertinoWheel,
        ).expandir(),
      ].fila(espaciado: 12, mainAxisSize: MainAxisSize.max).maxAncho(400).padXY(0, 6),

      CustomDateRangePicker(
        label: "Periodo de vacaciones",
        hint: "Seleccionar rango",
        fillColor: colores.fondoSecundario,
      ).maxAncho(400).padXY(0, 6),

      CustomBottomSheetPicker<String>(
        label: "Departamento / Área (Modal con Búsqueda)",
        hint: "Selecciona tu área",
        sheetTitle: "Seleccionar Departamento",
        isSearchable: true,
        prefixIcon: Icons.business_outlined,
        fillColor: colores.fondoSecundario,
        items: const [
          PickerItem(value: "ti", label: "Tecnología e Informática", subtitle: "Desarrollo y DevOps", icon: Icons.code),
          PickerItem(value: "mkt", label: "Marketing & Growth", subtitle: "Publicidad y Redes", icon: Icons.campaign_outlined),
          PickerItem(value: "ventas", label: "Ventas Comerciales", subtitle: "Cuentas Clave", icon: Icons.attach_money),
        ],
      ).maxAncho(400).padXY(0, 16),

      // 6. INTERRUPTORES (SWITCHES SUITE)
      "Interruptores (Switches)".texto(size: textos.subtitulo.fontSize!, color: colores.textoPrincipal, negrita: true).padSolo(b: 10),

      CustomSwitchCard(
        title: "Notificaciones Push",
        description: "Recibe alertas en tiempo real sobre tu cuenta",
        icon: Icons.notifications_active_outlined,
        value: true,
        onChanged: (val) {},
      ).maxAncho(400).padXY(0, 6),

      CustomSwitchTile(
        title: "Sincronización en segundo plano",
        subtitle: "Mantén tus datos actualizados siempre",
        leadingIcon: Icons.sync,
        value: true,
        hasBackground: true,
        hasBorder: true,
        onChanged: (val) {},
      ).maxAncho(400).padXY(0, 6),

      [
        CustomSwitch(value: true, onChanged: (val) {}),
        CustomIconSwitch.tema(esOscuro: false, onChanged: (val) {}),
        CustomIconSwitch.notificaciones(activadas: true, onChanged: (val) {}),
        CustomAsyncSwitch(
          initialValue: false,
          onAsyncChanged: (val) async {
            await Future.delayed(const Duration(milliseconds: 1000));
            return true;
          },
        ),
      ].fila(espaciado: 16, mainAxis: MainAxisAlignment.center, mainAxisSize: MainAxisSize.min).padXY(0, 16),

      // 7. BARRAS DESLIZABLES (SLIDERS SUITE)
      "Barras Deslizables (Sliders)".texto(size: textos.subtitulo.fontSize!, color: colores.textoPrincipal, negrita: true).padSolo(b: 10),

      CustomSlider(
        headerTitle: "Nivel de Satisfacción",
        value: 85.0,
        showValueIndicator: true,
        valueFormatter: (val) => "${val.toInt()}%",
        onChanged: (val) {},
      ).maxAncho(400).padXY(0, 4),

      CustomSliderCard(
        title: "Uso de Almacenamiento",
        description: "Espacio ocupado en tu cuenta en la nube",
        icon: Icons.cloud_queue_outlined,
        value: 68.0,
        onChanged: (val) {},
      ).maxAncho(400).padXY(0, 6),

      CustomRangeSlider(
        headerTitle: "Rango de Presupuesto",
        values: const RangeValues(150, 750),
        min: 0,
        max: 1000,
        divisions: 20,
        valueFormatter: (range) => "\$${range.start.toInt()} - \$${range.end.toInt()}",
        onChanged: (val) {},
      ).maxAncho(400).padXY(0, 6),

      CustomIconSlider.volumen(value: 75.0, onChanged: (val) {}).maxAncho(400).padXY(0, 4),
      CustomIconSlider.brillo(value: 45.0, onChanged: (val) {}).maxAncho(400).padXY(0, 4),

      CustomDiscreteSlider(
        headerTitle: "Nivel de Experiencia",
        value: 2,
        steps: const ["Junior", "Mid", "Senior", "Lead"],
        onChanged: (val) {},
      ).maxAncho(400).padXY(0, 16),

      // 8. BOTONES ESTANDARIZADOS (BUTTONS SUITE)
      "Colección de Botones".texto(size: textos.subtitulo.fontSize!, color: colores.textoPrincipal, negrita: true).padSolo(b: 10),

      [
        CustomPrimaryButton(text: "Guardar", icon: Icons.check_circle_outline, onPressed: () {}).expandir(),
        CustomSecondaryButton(text: "Exportar", icon: Icons.file_download_outlined, onPressed: () {}).expandir(),
      ].fila(espaciado: 12, mainAxisSize: MainAxisSize.max).maxAncho(400).padXY(0, 6),

      [
        CustomOutlineButton(text: "Cancelar", onPressed: () {}).expandir(),
        CustomDangerButton(text: "Eliminar", icon: Icons.delete_outline, onPressed: () {}).expandir(),
      ].fila(espaciado: 12, mainAxisSize: MainAxisSize.max).maxAncho(400).padXY(0, 6),

      [
        const CustomPrimaryButton(text: "Cargando...", isLoading: true, width: 140),
        CustomTextButton(text: "¿Necesitas ayuda?", icon: Icons.help_outline, onPressed: () {}),
      ].fila(espaciado: 15, mainAxis: MainAxisAlignment.center, mainAxisSize: MainAxisSize.min).padXY(0, 6),

      [
        CustomIconButton(icon: Icons.favorite_border, isCircle: true, isOutline: true, onPressed: () {}),
        CustomIconButton(icon: Icons.share_outlined, isCircle: true, isSecondary: true, onPressed: () {}),
        CustomIconButton(icon: Icons.edit_outlined, isCircle: true, onPressed: () {}),
        CustomIconButton(icon: Icons.delete_outline, isCircle: true, isDanger: true, isOutline: true, onPressed: () {}),
      ].fila(espaciado: 15, mainAxis: MainAxisAlignment.center, mainAxisSize: MainAxisSize.min).padXY(0, 16),

      // 9. DIÁLOGOS DE ALERTA Y MODALES (ALERT DIALOGS SUITE)
      "Ventanas Emergentes (Alert Dialogs)".texto(size: textos.subtitulo.fontSize!, color: colores.textoPrincipal, negrita: true).padSolo(b: 10),

      [
        CustomOutlineButton(
          text: "Confirmación",
          icon: Icons.help_outline,
          onPressed: () => CustomConfirmationDialog.show(
            context: context,
            title: "¿Cerrar Sesión?",
            message: "¿Estás seguro de que deseas salir de tu cuenta activa?",
            confirmText: "Salir",
          ),
        ).expandir(),

        CustomDangerButton(
          text: "Crítico / Borrar",
          icon: Icons.delete_forever_outlined,
          onPressed: () => CustomDangerDialog.show(
            context: context,
            title: "¿Eliminar Proyecto?",
            message: "Esta acción borrará todas las bases de datos y no se puede deshacer.",
            requireConfirmationWord: "BORRAR",
          ),
        ).expandir(),
      ].fila(espaciado: 12, mainAxisSize: MainAxisSize.max).maxAncho(400).padXY(0, 6),

      [
        CustomPrimaryButton(
          text: "Éxito / Pago",
          icon: Icons.check_circle_outline,
          backgroundColor: colores.exito,
          onPressed: () => CustomSuccessDialog.show(
            context: context,
            title: "¡Pago Confirmado!",
            message: "Tu suscripción Pro ha sido activada con éxito.",
          ),
        ).expandir(),

        CustomPrimaryButton(
          text: "Advertencia",
          icon: Icons.warning_amber_rounded,
          backgroundColor: colores.advertencia,
          onPressed: () => CustomWarningDialog.show(
            context: context,
            title: "Espacio Insuficiente",
            message: "Has consumido el 95% del almacenamiento asignado en la nube.",
          ),
        ).expandir(),
      ].fila(espaciado: 12, mainAxisSize: MainAxisSize.max).maxAncho(400).padXY(0, 6),

      [
        CustomSecondaryButton(
          text: "Prompt / Input",
          icon: Icons.edit_note,
          onPressed: () => CustomInputDialog.show(
            context: context,
            title: "Nueva Carpeta",
            message: "Ingresa un nombre representativo para la carpeta:",
            hint: "Ej. Diseños 2026",
          ),
        ).expandir(),

        CustomSecondaryButton(
          text: "Carga Bloqueante",
          icon: Icons.hourglass_top_outlined,
          onPressed: () async {
            CustomLoadingDialog.show(context, message: "Sincronizando datos...");
            await Future.delayed(const Duration(milliseconds: 2000));
            if (context.mounted) {
              CustomLoadingDialog.hide(context);
            }
          },
        ).expandir(),
      ].fila(espaciado: 12, mainAxisSize: MainAxisSize.max).maxAncho(400).padXY(0, 6),

      CustomTextButton(
        text: "Ver Diálogo Informativo",
        icon: Icons.info_outline,
        onPressed: () => CustomInfoDialog.show(
          context: context,
          title: "Versión 2.0 Lista",
          message: "Hemos actualizado todo el motor de UI a una arquitectura declarativa orientada a objetos.",
        ),
      ).padXY(0, 14),

      // 10. COMPONENTES DESLIZABLES (SWIPE-TO-DISMISS / GMAIL STYLE)
      "Deslizar para Acciones (Swipe-to-Dismiss)"
          .texto(size: textos.subtitulo.fontSize!, color: colores.textoPrincipal, negrita: true)
          .padSolo(b: 10),

      // 1. Tarjeta deslizable de notificación (con confirmación de borrado)
      CustomDismissibleCard(
        itemKey: const ValueKey("dismiss_card_1"),
        title: "Nuevo mensaje de soporte técnico",
        subtitle: "Desliza a la izquierda para borrar o a la derecha para archivar.",
        time: "Hace 5m",
        leadingIcon: Icons.mark_email_unread_outlined,
        isUnread: true,
        confirmOnDelete: true,
        onDelete: () {},
        onArchive: () {},
      ).maxAncho(400).padXY(0, 5),

      // 2. Tarjeta de Solicitud de Decisión (Deslizar Derecha = Aceptar / Izquierda = Rechazar)
      CustomDismissibleCard.decision(
        itemKey: const ValueKey("dismiss_decision_1"),
        title: "Carlos Mendoza solicita unirse al equipo",
        subtitle: "Desliza a la DERECHA para Aceptar o a la IZQUIERDA para Rechazar.",
        time: "10:30 AM",
        leadingIcon: Icons.person_add_outlined,
        leadingColor: colores.primario,
        confirmOnDelete: true,
        onAccept: () {},
        onReject: () {},
      ).maxAncho(400).padXY(0, 5),

      // 3. Tarjeta deslizable de tarea / pedido
      CustomDismissibleCard(
        itemKey: const ValueKey("dismiss_card_2"),
        title: "Revisar arquitectura móvil del proyecto",
        subtitle: "Completado y sincronizado con el repositorio.",
        time: "Hoy",
        leadingIcon: Icons.task_alt_rounded,
        leadingColor: colores.exito,
        onDelete: () {},
        onArchive: () {},
      ).maxAncho(400).padXY(0, 5),

      // 4. Tarjeta abstracta CustomInfoCard vuelta deslizable con el modificador .deslizable()
      const CustomInfoCard(
        title: "Tarjeta Abstracta con .deslizable()",
        description: "Aplica el modificador sobre cualquier abstracción del sistema.",
        icon: Icons.swipe_outlined,
      ).deslizable(
        key: const ValueKey("card_info_dismiss"),
        onEliminar: () {},
        onArchivar: () {},
      ).maxAncho(400).padXY(0, 14),

      // 11. CUADRÍCULAS Y MATRICES (GRID VIEW SUITE)
      "Cuadrículas y Matrices (Grid View)"
          .texto(size: textos.subtitulo.fontSize!, color: colores.textoPrincipal, negrita: true)
          .padSolo(b: 10),

      // 1. Matriz de Accesos Rápidos (Menús y Apps Bancarias)
      "Matriz de Accesos Rápidos"
          .texto(size: textos.cuerpoPequeno.fontSize!, color: colores.textoSecundario, negrita: true)
          .padSolo(b: 6),

      CustomMatrixGrid(
        crossAxisCount: 4,
        items: [
          CustomMatrixItem(
            label: "Transferir",
            icon: Icons.send_rounded,
            color: colores.primario,
            onTap: () {},
          ),
          CustomMatrixItem(
            label: "Pagar",
            icon: Icons.receipt_long_rounded,
            color: colores.exito,
            badgeCount: 2,
            onTap: () {},
          ),
          CustomMatrixItem(
            label: "Código QR",
            icon: Icons.qr_code_scanner_rounded,
            color: colores.secundario,
            onTap: () {},
          ),
          CustomMatrixItem(
            label: "Inversiones",
            icon: Icons.trending_up_rounded,
            color: colores.advertencia,
            onTap: () {},
          ),
          CustomMatrixItem(
            label: "Servicios",
            icon: Icons.electrical_services_rounded,
            onTap: () {},
          ),
          CustomMatrixItem(
            label: "Recargas",
            icon: Icons.phone_android_rounded,
            onTap: () {},
          ),
          CustomMatrixItem(
            label: "Soporte",
            icon: Icons.headset_mic_outlined,
            onTap: () {},
          ),
          CustomMatrixItem(
            label: "Ajustes",
            icon: Icons.tune_rounded,
            onTap: () {},
          ),
        ],
      ).maxAncho(400).padXY(0, 10),

      // 2. Galería Multimedia de Fotos y Videos
      "Galería Multimedia (+N Fotos y Videos)"
          .texto(size: textos.cuerpoPequeno.fontSize!, color: colores.textoSecundario, negrita: true)
          .padSolo(t: 6, b: 6),

      CustomMediaGrid(
        crossAxisCount: 3,
        maxVisibleItems: 6,
        items: const [
          CustomMediaItem(title: "Foto 1"),
          CustomMediaItem(title: "Video 1", isVideo: true, videoDuration: "02:45"),
          CustomMediaItem(title: "Foto 2", isSelected: true),
          CustomMediaItem(title: "Foto 3"),
          CustomMediaItem(title: "Video 2", isVideo: true, videoDuration: "00:50"),
          CustomMediaItem(title: "Foto 4"),
          CustomMediaItem(title: "Foto 5"),
          CustomMediaItem(title: "Foto 6"),
          CustomMediaItem(title: "Foto 7"),
        ],
      ).maxAncho(400).padXY(0, 10),

      // 3. Cuadrícula de Métricas y KPIs de Dashboard
      "Métricas de Rendimiento (Dashboard)"
          .texto(size: textos.cuerpoPequeno.fontSize!, color: colores.textoSecundario, negrita: true)
          .padSolo(t: 6, b: 6),

      CustomStatsGrid(
        crossAxisCount: 2,
        childAspectRatio: 1.35,
        stats: const [
          CustomStatCard(
            title: "Ingresos Totales",
            value: "\$48,920",
            icon: Icons.attach_money_rounded,
            trendText: "+18.4%",
            isPositiveTrend: true,
          ),
          CustomStatCard(
            title: "Nuevos Clientes",
            value: "1,248",
            icon: Icons.people_outline_rounded,
            trendText: "+12.1%",
            isPositiveTrend: true,
          ),
        ],
      ).maxAncho(400).padXY(0, 20),

      // 12. SISTEMA DE ANIMACIONES Y LOADERS
      "Animaciones y Esqueletos (Loaders)"
          .texto(size: textos.subtitulo.fontSize!, color: colores.textoPrincipal, negrita: true)
          .padSolo(t: 20, b: 10),

      // Esqueleto de Tarjeta Completa (Card Skeleton)
      "Skeleton Loader (Tarjeta Completa)"
          .texto(size: textos.cuerpoPequeno.fontSize!, color: colores.textoSecundario, negrita: true)
          .padSolo(b: 6),
      CustomSkeleton.card().maxAncho(400).padXY(0, 10),

      // Esqueleto de Elemento de Lista (ListTile Skeleton)
      "Skeleton Loader (Elemento de Lista)"
          .texto(size: textos.cuerpoPequeno.fontSize!, color: colores.textoSecundario, negrita: true)
          .padSolo(b: 6),
      CustomSkeleton.listTile().maxAncho(400).padXY(0, 10),

      // Otros Loaders Básicos
      "Indicadores de Carga (Lineal, Circular y Puntos)"
          .texto(size: textos.cuerpoPequeno.fontSize!, color: colores.textoSecundario, negrita: true)
          .padSolo(b: 10),

      [
        CustomLoaderLinear().expandir(),
        CustomLoaderDots(size: 10).padXY(20, 0),
        const CustomSpinner(size: 24),
      ].fila(espaciado: 12, mainAxisSize: MainAxisSize.max).maxAncho(400).padXY(0, 10),
      
      // Loaders Complejos / Específicos
      "Loaders Especializados (Olas, Pulso y Typing)"
          .texto(size: textos.cuerpoPequeno.fontSize!, color: colores.textoSecundario, negrita: true)
          .padSolo(b: 10),
          
      [
        const CustomLoaderWave(barsCount: 5).expandir(),
        const CustomLoaderPulse(size: 40).expandir(),
        const CustomLoaderTyping().expandir(),
      ].fila(espaciado: 12, mainAxisSize: MainAxisSize.max).maxAncho(400).padXY(0, 10),
      
      "Overlay de Carga (Carga bloqueante en Tarjetas)"
          .texto(size: textos.cuerpoPequeno.fontSize!, color: colores.textoSecundario, negrita: true)
          .padSolo(b: 10),
          
      CustomLoaderOverlay(
        isLoading: true,
        loadingText: "Procesando datos...",
        child: const CustomInfoCard(
          title: "Tarjeta Bloqueada",
          description: "Esta tarjeta está envuelta en un CustomLoaderOverlay(isLoading: true) que impide interactuar con ella.",
          icon: Icons.lock,
        ),
      ).maxAncho(400).padXY(0, 10),

      // Componentes con Animaciones Interactivas
      "Animaciones Modulares (Interactivas)"
          .texto(size: textos.cuerpoPequeno.fontSize!, color: colores.textoSecundario, negrita: true)
          .padSolo(t: 10, b: 10),

      const _BotonesAnimados(),
      
      // 13. INTERACCIÓN MULTIMEDIA
      "Interacción Multimedia"
          .texto(size: textos.subtitulo.fontSize!, color: colores.textoPrincipal, negrita: true)
          .padSolo(t: 20, b: 10),

      "Avatares de Usuario con Estados"
          .texto(size: textos.cuerpoPequeno.fontSize!, color: colores.textoSecundario, negrita: true)
          .padSolo(b: 10),
      
      [
        const CustomAvatar(initials: "JD", status: AvatarStatus.online),
        const CustomAvatar(initials: "MK", status: AvatarStatus.away, backgroundColor: Colors.orangeAccent),
        const CustomAvatar(initials: "AL", status: AvatarStatus.busy, backgroundColor: Colors.redAccent),
        const CustomAvatar(initials: "RO", status: AvatarStatus.offline, backgroundColor: Colors.grey),
      ].fila(espaciado: 16, mainAxis: MainAxisAlignment.spaceEvenly).maxAncho(400).padSolo(b: 16),

      "Selectores Multimedia (Pickers Nativos)"
          .texto(size: textos.cuerpoPequeno.fontSize!, color: colores.textoSecundario, negrita: true)
          .padSolo(b: 10),
          
      [
        CustomMediaPicker(
          text: "Tomar Foto", 
          type: MediaType.image,
          onFilesSelected: (files) {
            debugPrint("Archivos seleccionados: \$files");
          },
        ).expandir(),
        const CustomMediaPicker(text: "Subir Archivo", type: MediaType.document, isSecondary: true).expandir(),
      ].fila(espaciado: 12, mainAxisSize: MainAxisSize.max).maxAncho(400).padSolo(b: 16),

      "Visor Interactivo (Pinch to Zoom)"
          .texto(size: textos.cuerpoPequeno.fontSize!, color: colores.textoSecundario, negrita: true)
          .padSolo(b: 6),
          
      "Visor Interactivo (Pinch to Zoom)"
          .texto(size: textos.cuerpoPequeno.fontSize!, color: colores.textoSecundario, negrita: true)
          .padSolo(b: 6),
          
      CustomInteractiveViewer.icono(icono: Icons.pinch_outlined, size: 100)
       .h(250).w(double.infinity)
       .estilo(bg: colores.fondoSecundario, bordeColor: colores.borde, radio: 12)
       .maxAncho(400).padSolo(b: 20),
      
      const SizedBox(height: 60).ocultar(false), // O alternativamente [].columna().h(60)

    ].columna();
  }
}

// Widget interno para demostrar la interactividad de las animaciones
class _BotonesAnimados extends StatefulWidget {
  const _BotonesAnimados();

  @override
  State<_BotonesAnimados> createState() => _BotonesAnimadosState();
}

class _BotonesAnimadosState extends State<_BotonesAnimados> {
  int _contadorRebote = 0;
  int _contadorError = 0;
  bool _mostrarTarjeta = false;

  @override
  Widget build(BuildContext context) {
    final colores = context.colores;
    
    return [
      [
        CustomPrimaryButton(
          key: ValueKey('rebote_$_contadorRebote'),
          text: "Rebote (Pop)", 
          onPressed: () => setState(() => _contadorRebote++),
        )
        .animarRebote()
        .expandir(),
        
        CustomDangerButton(
          key: ValueKey('error_$_contadorError'),
          text: "Error (Shake)", 
          onPressed: () => setState(() => _contadorError++),
        )
        .animarError(activar: true)
        .expandir(),
      ].fila(espaciado: 12, mainAxisSize: MainAxisSize.max).maxAncho(400).padXY(0, 6),
      
      CustomSecondaryButton(
        text: _mostrarTarjeta ? "Ocultar Tarjeta" : "Mostrar Tarjeta", 
        icon: _mostrarTarjeta ? Icons.visibility_off : Icons.visibility,
        onPressed: () => setState(() => _mostrarTarjeta = !_mostrarTarjeta),
      ).maxAncho(400).padSolo(t: 16),
      
      if (_mostrarTarjeta)
        const CustomInfoCard(
          title: "Heredando flutter_animate",
          description: "Combina abstracciones. Usa .animarEntrada() y encadena un .shake() y .tint() crudos de la librería nativa.",
          icon: Icons.auto_awesome,
        ).maxAncho(400).padSolo(t: 16, b: 6)
         .animarEntrada(delay: 100.ms) // Entra suave
         .shake(delay: 800.ms, hz: 3) // Encadenado nativo
         .tint(color: colores.primario, end: 0.2, duration: 400.ms)
         .then()
         .tint(color: Colors.transparent),
    ].columna();
  }
}

class _SimpsonsApiDemo extends StatefulWidget {
  const _SimpsonsApiDemo();

  @override
  State<_SimpsonsApiDemo> createState() => _SimpsonsApiDemoState();
}

class _SimpsonsApiDemoState extends State<_SimpsonsApiDemo> {
  bool _isLoading = false;
  List<dynamic> _characters = [];
  String _error = "";

  Future<void> _fetchCharacters() async {
    setState(() {
      _isLoading = true;
      _error = "";
    });

    try {
      final response = await api.get('/characters', queryParameters: {'page': 1});
      setState(() {
        _characters = response['results'] ?? [];
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final colores = context.colores;
    final textos = context.textos;

    return [
      "Prueba de ApiProvider (The Simpsons)"
          .texto(size: textos.subtitulo.fontSize!, color: colores.textoPrincipal, negrita: true),
          
      "Demostración de abstracción de red"
          .texto(size: textos.cuerpoPequeno.fontSize!, color: colores.textoSecundario)
          .padSolo(t: 8, b: 16),
          
      CustomPrimaryButton(
        text: _isLoading ? "Cargando..." : "GET /api/characters",
        icon: Icons.cloud_download_outlined,
        isLoading: _isLoading,
        onPressed: _fetchCharacters,
      ).w(double.infinity),
      
      if (_error.isNotEmpty) 
        _error.texto(size: textos.cuerpoPequeno.fontSize!, color: colores.error).padSolo(t: 16),
      
      if (_characters.isNotEmpty) ...[
        "Resultados de la página 1 (${_characters.length}):"
            .texto(size: textos.cuerpoPequeno.fontSize!, color: colores.textoPrincipal, negrita: true)
            .padSolo(t: 16, b: 8),
            
        _characters.map((char) {
          final nombre = char['name'] ?? 'Desconocido';
          final inicial = nombre.toString().isNotEmpty ? nombre.toString().substring(0, 1) : '?';
          final frases = char['phrases'] as List<dynamic>? ?? [];

          return [
            CustomAvatar(initials: inicial, backgroundColor: colores.primario),
            [
              nombre.toString().texto(color: colores.textoPrincipal, negrita: true),
              (char['occupation'] ?? 'Sin ocupación').toString().texto(color: colores.textoSecundario, size: 12),
            ].columna(crossAxis: CrossAxisAlignment.start).expandir(),
          ].fila(espaciado: 12)
           .pad(12)
           .click(() async {
               CustomLoadingDialog.show(context, message: 'Cargando detalle...');
               try {
                 final detRes = await api.get('/characters/${char['id']}');
                 if (context.mounted) CustomLoadingDialog.hide(context);
                 
                 if (context.mounted) {
                    CustomInfoDialog.show(
                      context: context,
                      title: "Detalle: \$nombre",
                      message: "ID: \${detRes['id']}\nEstado: \${detRes['status']}\nFrase: \${frases.isNotEmpty ? frases.first : 'Ninguna'}",
                    );
                 }
               } catch (e) {
                 if (context.mounted) CustomLoadingDialog.hide(context);
                 if (context.mounted) {
                    CustomWarningDialog.show(context: context, title: "Error", message: e.toString());
                 }
               }
           });
        }).toList()
          .columna()
          .scroll()
          .h(250)
          .estilo(bordeColor: colores.borde, radio: 8),
      ]
    ].columna(crossAxis: CrossAxisAlignment.start)
     .pad(16)
     .estilo(bg: colores.fondoSecundario, radio: 16, bordeColor: colores.borde)
     .maxAncho(400)
     .padXY(0, 16);
  }
}
