import 'package:flutter/material.dart';

class EntityCard extends StatelessWidget {
  final String title;
  final String? subtitle;
  final String? trailingText;
  final IconData leadingIcon;
  final VoidCallback onTap;
  final VoidCallback? onEdit;
  final VoidCallback? onDelete;

  const EntityCard({
    super.key,
    required this.title,
    this.subtitle,
    this.trailingText,
    this.leadingIcon = Icons.layers_outlined,
    required this.onTap,
    this.onEdit,
    this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        leading: CircleAvatar(
          backgroundColor: const Color(0xFF2563EB).withValues(alpha: 0.15),
          child: Icon(leadingIcon, color: const Color(0xFF38BDF8), size: 20),
        ),
        title: Text(
          title,
          style: const TextStyle(color: Color(0xFFF8FAFC), fontWeight: FontWeight.w600, fontSize: 15),
        ),
        subtitle: subtitle != null
            ? Text(
                subtitle!,
                style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              )
            : null,
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (trailingText != null)
              Padding(
                padding: const EdgeInsets.only(right: 8.0),
                child: Text(
                  trailingText!,
                  style: const TextStyle(color: Color(0xFF38BDF8), fontWeight: FontWeight.bold),
                ),
              ),
            if (onEdit != null)
              IconButton(
                icon: const Icon(Icons.edit_outlined, size: 18, color: Color(0xFF94A3B8)),
                onPressed: onEdit,
                tooltip: 'Editar',
              ),
            if (onDelete != null)
              IconButton(
                icon: const Icon(Icons.delete_outline, size: 18, color: Color(0xFFEF4444)),
                onPressed: onDelete,
                tooltip: 'Eliminar',
              ),
          ],
        ),
        onTap: onTap,
      ),
    );
  }
}

