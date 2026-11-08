import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';
import 'custom_card.dart';

/// Tarjeta de Perfil / Usuario (`CustomProfileCard`):
/// Ideal para listas de contactos, miembros de equipo, perfiles o líderes de proyecto.
class CustomProfileCard extends StatelessWidget {
  final String name;
  final String role;
  final String? company;
  final String? bio;
  final Widget? avatarWidget;
  final IconData avatarIcon;
  final bool isOnline;
  final List<String>? tags;
  final Widget? actionButton;
  final VoidCallback? onTap;

  const CustomProfileCard({
    super.key,
    required this.name,
    required this.role,
    this.company,
    this.bio,
    this.avatarWidget,
    this.avatarIcon = Icons.person,
    this.isOnline = false,
    this.tags,
    this.actionButton,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final themeTextos = context.textos;

    return CustomCard(
      onTap: onTap,
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              // Avatar con indicador de estado (Online)
              Stack(
                children: [
                  Container(
                    width: 50,
                    height: 50,
                    decoration: BoxDecoration(
                      color: themeColores.primario.withValues(alpha: 0.12),
                      shape: BoxShape.circle,
                    ),
                    child: avatarWidget ??
                        Icon(
                          avatarIcon,
                          color: themeColores.primario,
                          size: 28,
                        ),
                  ),
                  if (isOnline)
                    Positioned(
                      right: 0,
                      bottom: 0,
                      child: Container(
                        width: 13,
                        height: 13,
                        decoration: BoxDecoration(
                          color: themeColores.exito,
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: themeColores.fondoSecundario,
                            width: 2,
                          ),
                        ),
                      ),
                    ),
                ],
              ),
              const SizedBox(width: 14),

              // Nombre y Rol
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      name,
                      style: themeTextos.cuerpo.copyWith(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      company != null ? "$role • $company" : role,
                      style: themeTextos.cuerpoPequeno.copyWith(
                        color: themeColores.textoSecundario,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),

              // Botón de acción opcional
              if (actionButton != null) ...[
                const SizedBox(width: 8),
                actionButton!,
              ],
            ],
          ),

          // Biografía o descripción breve
          if (bio != null) ...[
            const SizedBox(height: 12),
            Text(
              bio!,
              style: themeTextos.cuerpoPequeno.copyWith(
                color: themeColores.textoSecundario,
                fontSize: 13,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ],

          // Etiquetas de habilidades / tags
          if (tags != null && tags!.isNotEmpty) ...[
            const SizedBox(height: 12),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: tags!.map((tag) {
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: themeColores.borde.withValues(alpha: 0.4),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    tag,
                    style: themeTextos.cuerpoPequeno.copyWith(
                      fontSize: 11,
                      color: themeColores.textoPrincipal,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                );
              }).toList(),
            ),
          ],
        ],
      ),
    );
  }
}
