import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';

/// Barra Superior con Perfil de Usuario (`CustomProfileAppBar`):
/// Ideal para la pantalla de inicio principal (Home / Dashboard),
/// mostrando el avatar del usuario, saludo personalizado y botones de acción (notificaciones, alertas).
class CustomProfileAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String userName;
  final String? greeting;
  final String? avatarUrl;
  final Widget? avatarWidget;
  final bool isOnline;
  final List<Widget>? actions;
  final VoidCallback? onAvatarTap;
  final Color? backgroundColor;

  const CustomProfileAppBar({
    super.key,
    required this.userName,
    this.greeting = "¡Hola de nuevo!",
    this.avatarUrl,
    this.avatarWidget,
    this.isOnline = true,
    this.actions,
    this.onAvatarTap,
    this.backgroundColor,
  });

  @override
  Size get preferredSize => const Size.fromHeight(68.0);

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;

    return AppBar(
      backgroundColor: backgroundColor ?? themeColores.fondo,
      elevation: 0,
      titleSpacing: 16,
      automaticallyImplyLeading: false,
      title: Row(
        children: [
          // 1. Avatar con badge de estado
          GestureDetector(
            onTap: onAvatarTap,
            child: Stack(
              children: [
                if (avatarWidget != null)
                  avatarWidget!
                else if (avatarUrl != null && avatarUrl!.isNotEmpty)
                  CircleAvatar(
                    radius: 22,
                    backgroundImage: NetworkImage(avatarUrl!),
                  )
                else
                  CircleAvatar(
                    radius: 22,
                    backgroundColor: themeColores.primario.withValues(alpha: 0.15),
                    child: Text(
                      userName.isNotEmpty ? userName[0].toUpperCase() : "U",
                      style: TextStyle(
                        color: themeColores.primario,
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                  ),

                // Punto indicador de estado activo
                if (isOnline)
                  Positioned(
                    bottom: 0,
                    right: 0,
                    child: Container(
                      width: 12,
                      height: 12,
                      decoration: BoxDecoration(
                        color: themeColores.exito,
                        shape: BoxShape.circle,
                        border: Border.all(color: themeColores.fondo, width: 2),
                      ),
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(width: 12),

          // 2. Saludo y Nombre del Usuario
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                if (greeting != null)
                  Text(
                    greeting!,
                    style: themeTextos.cuerpoPequeno.copyWith(
                      color: themeColores.textoSecundario,
                      fontSize: 12,
                    ),
                  ),
                Text(
                  userName,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: themeTextos.titulo.copyWith(
                    fontSize: 17,
                    fontWeight: FontWeight.bold,
                    color: themeColores.textoPrincipal,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
      actions: actions,
    );
  }
}
