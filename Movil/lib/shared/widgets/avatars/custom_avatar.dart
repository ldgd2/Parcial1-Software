import 'package:flutter/material.dart';
import '../../utils/ui_engine/tema.dart';

enum AvatarStatus {
  online,
  offline,
  busy,
  away,
  none, // Sin estado visible
}

/// Avatar de usuario con soporte para estados (conectado, desconectado, etc.),
/// iniciales de texto si no hay imagen, e imágenes por red o archivo.
class CustomAvatar extends StatelessWidget {
  final String? imageUrl;
  final String? initials;
  final double size;
  final AvatarStatus status;
  final Color? backgroundColor;
  final Color? textColor;

  const CustomAvatar({
    super.key,
    this.imageUrl,
    this.initials,
    this.size = 48.0,
    this.status = AvatarStatus.none,
    this.backgroundColor,
    this.textColor,
  });

  /// Variante pequeña para listas o chats
  const CustomAvatar.small({
    super.key,
    this.imageUrl,
    this.initials,
    this.status = AvatarStatus.none,
    this.backgroundColor,
    this.textColor,
  }) : size = 32.0;

  /// Variante grande para pantallas de perfil
  const CustomAvatar.large({
    super.key,
    this.imageUrl,
    this.initials,
    this.status = AvatarStatus.none,
    this.backgroundColor,
    this.textColor,
  }) : size = 120.0;

  Color _getStatusColor(BuildContext context) {
    switch (status) {
      case AvatarStatus.online:
        return Colors.green;
      case AvatarStatus.busy:
        return Colors.red;
      case AvatarStatus.away:
        return Colors.orange;
      case AvatarStatus.offline:
        return Colors.grey;
      case AvatarStatus.none:
      default:
        return Colors.transparent;
    }
  }

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final textos = context.textos;

    final bgColor = backgroundColor ?? themeColores.primario.withValues(alpha: 0.1);
    final fgColor = textColor ?? themeColores.primario;
    
    // El tamaño del estado es proporcional al avatar
    final statusSize = size * 0.25;

    Widget avatarImage = CircleAvatar(
      radius: size / 2,
      backgroundColor: bgColor,
      backgroundImage: imageUrl != null ? NetworkImage(imageUrl!) : null,
      child: imageUrl == null
          ? Text(
              initials ?? '?',
              style: textos.cuerpo.copyWith(
                color: fgColor,
                fontWeight: FontWeight.bold,
                fontSize: size * 0.4, // El texto se ajusta al círculo
              ),
            )
          : null,
    );

    if (status == AvatarStatus.none) {
      return avatarImage;
    }

    return Stack(
      children: [
        avatarImage,
        Positioned(
          right: 0,
          bottom: 0,
          child: Container(
            width: statusSize,
            height: statusSize,
            decoration: BoxDecoration(
              color: _getStatusColor(context),
              shape: BoxShape.circle,
              border: Border.all(
                color: themeColores.fondoSecundario,
                width: size * 0.05, // Borde blanco/oscuro proporcional
              ),
            ),
          ),
        ),
      ],
    );
  }
}
