import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:file_picker/file_picker.dart';
import '../../utils/ui_engine/tema.dart';

enum MediaType { image, video, document, any }

/// Un botón especializado para abrir el selector nativo del SO (Cámara o Galería).
/// Requiere `image_picker` y `file_picker` configurados en Android/iOS.
class CustomMediaPicker extends StatelessWidget {
  final String text;
  final MediaType type;
  final bool allowMultiple;
  final Function(List<String> filePaths)? onFilesSelected;
  final IconData? icon;
  final bool isSecondary;

  const CustomMediaPicker({
    super.key,
    required this.text,
    this.type = MediaType.image,
    this.allowMultiple = false,
    this.onFilesSelected,
    this.icon,
    this.isSecondary = false,
  });

  Future<void> _pickMedia(BuildContext context) async {
    List<String> paths = [];

    try {
      if (type == MediaType.image || type == MediaType.video) {
        final ImagePicker picker = ImagePicker();
        if (allowMultiple && type == MediaType.image) {
          final List<XFile> images = await picker.pickMultiImage();
          paths = images.map((e) => e.path).toList();
        } else {
          final XFile? file = type == MediaType.image
              ? await picker.pickImage(source: ImageSource.gallery)
              : await picker.pickVideo(source: ImageSource.gallery);
          if (file != null) paths.add(file.path);
        }
      } else {
        // Documentos o cualquier archivo
        final FileType fileType = type == MediaType.document ? FileType.custom : FileType.any;
        final List<String> allowedExtensions = type == MediaType.document ? ['pdf', 'doc', 'docx', 'txt'] : [];

        final List<PlatformFile> result = await FilePicker.pickFiles(
          allowMultiple: allowMultiple,
          type: fileType,
          allowedExtensions: allowedExtensions.isNotEmpty ? allowedExtensions : null,
        ) ?? [];

        if (result.isNotEmpty) {
          paths = result.where((file) => file.path != null).map((file) => file.path!).toList();
        }
      }

      if (paths.isNotEmpty && onFilesSelected != null) {
        onFilesSelected!(paths);
      }
    } catch (e) {
      debugPrint("Error seleccionando archivo: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    final themeColores = context.colores;
    final textos = context.textos;

    final IconData defaultIcon = type == MediaType.image
        ? Icons.photo_library
        : (type == MediaType.video ? Icons.video_library : Icons.attach_file);

    final fgColor = isSecondary ? themeColores.textoPrincipal : Colors.white;
    final bgColor = isSecondary ? themeColores.borde : themeColores.primario;

    return Material(
      color: bgColor,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: () => _pickMedia(context),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon ?? defaultIcon, color: fgColor, size: 20),
              const SizedBox(width: 12),
              Text(
                text,
                style: textos.boton.copyWith(color: fgColor),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
