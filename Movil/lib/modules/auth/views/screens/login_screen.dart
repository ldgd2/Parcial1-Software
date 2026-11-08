import 'package:flutter/material.dart';
import 'package:movil/core/storage/local_storage_service.dart';
import 'package:movil/core/network/api_provider.dart';
import 'package:movil/shared/utils/ui_engine/tema.dart';
import 'package:movil/shared/widgets/buttons/custom_button_primary.dart';
import 'package:movil/shared/widgets/buttons/custom_button_outline.dart';
import 'package:movil/shared/widgets/inputs/custom_input.dart';
import 'package:movil/shared/widgets/inputs/custom_input_email.dart';
import 'package:movil/shared/widgets/inputs/custom_input_password.dart';
import 'package:movil/modules/proyectos/proyectos_routes.dart';
import 'package:movil/modules/auth/controllers/auth_controller.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController(text: 'admin@test.com');
  final _passwordController = TextEditingController(text: 'Admin123*');
  final _invitadoController = TextEditingController();
  final _serverUrlController = TextEditingController();

  late final AuthController _authController;
  bool _modoInvitado = false;

  @override
  void initState() {
    super.initState();
    _authController = AuthController();
    _authController.addListener(_onAuthStateChanged);
    _serverUrlController.text = LocalStorageService.baseUrl;
  }

  @override
  void dispose() {
    _authController.removeListener(_onAuthStateChanged);
    _emailController.dispose();
    _passwordController.dispose();
    _invitadoController.dispose();
    _serverUrlController.dispose();
    super.dispose();
  }

  void _onAuthStateChanged() {
    if (mounted) setState(() {});
  }

  Future<void> _ejecutarLogin() async {
    if (!_formKey.currentState!.validate()) return;
    final exito = await _authController.login(
      _emailController.text,
      _passwordController.text,
    );
    if (exito && mounted) {
      Navigator.pushReplacementNamed(context, ProyectosRoutes.proyectos);
    }
  }

  Future<void> _ejecutarIngresoInvitado() async {
    final nombre = _invitadoController.text.trim();
    if (nombre.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ingresa un nombre para continuar')),
      );
      return;
    }
    final exito = await _authController.ingresoAnonimo(nombre);
    if (exito && mounted) {
      Navigator.pushReplacementNamed(context, ProyectosRoutes.proyectos);
    }
  }

  void _mostrarConfigurarServidor() {
    _serverUrlController.text = LocalStorageService.baseUrl;
    showDialog(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          backgroundColor: AppColores.oscuro.fondoSecundario,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          title: Text(
            'Servidor Backend',
            style: AppTextos.generar(AppColores.oscuro).titulo,
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              CustomInput(
                hint: 'https://api-diagramador.gerlextech.com',
                controller: _serverUrlController,
                prefixIcon: Icons.dns_outlined,
              ),
              const SizedBox(height: 8),
              Text(
                'Indica la URL base del backend (http:// o https://).',
                style: AppTextos.generar(AppColores.oscuro).cuerpoPequeno.copyWith(
                  color: AppColores.oscuro.secundario,
                  fontSize: 11,
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: Text('Cancelar', style: TextStyle(color: AppColores.oscuro.secundario)),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColores.oscuro.primario,
                foregroundColor: AppColores.oscuro.fondo,
              ),
              onPressed: () {
                api.actualizarBaseUrl(_serverUrlController.text);
                Navigator.pop(ctx);
                setState(() {});
              },
              child: const Text('Guardar'),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final colores = AppColores.oscuro;
    final textos = AppTextos.generar(colores);

    return Scaffold(
      backgroundColor: colores.fondo,
      appBar: AppBar(
        backgroundColor: colores.fondo,
        elevation: 0,
        actions: [
          IconButton(
            icon: Icon(Icons.settings_outlined, color: colores.secundario),
            tooltip: 'Ajustes de conexión',
            onPressed: _mostrarConfigurarServidor,
          ),
        ],
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 400),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Center(
                      child: Container(
                        width: 52,
                        height: 52,
                        alignment: Alignment.center,
                        decoration: BoxDecoration(
                          color: colores.fondoSecundario,
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: colores.borde),
                        ),
                        child: Icon(
                          Icons.schema_outlined,
                          size: 28,
                          color: colores.primario,
                        ),
                      ),
                    ),
                    const SizedBox(height: 14),
                    Text(
                      'Diagramador UML',
                      textAlign: TextAlign.center,
                      style: textos.tituloLargo,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Visor Móvil',
                      textAlign: TextAlign.center,
                      style: textos.cuerpoPequeno.copyWith(color: colores.secundario),
                    ),
                    const SizedBox(height: 28),

                    if (_authController.errorMessage != null) ...[
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: colores.error.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: colores.error.withValues(alpha: 0.5)),
                        ),
                        child: Text(
                          _authController.errorMessage!,
                          style: textos.cuerpoPequeno.copyWith(color: colores.error),
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],

                    if (!_modoInvitado) ...[
                      CustomEmailInput(
                        controller: _emailController,
                        label: 'Correo',
                        hint: 'correo@ejemplo.com',
                      ),
                      const SizedBox(height: 14),
                      CustomPasswordInput(
                        controller: _passwordController,
                        label: 'Contraseña',
                        hint: '••••••••',
                        validateRules: false,
                      ),
                      const SizedBox(height: 20),
                      CustomPrimaryButton(
                        text: 'Iniciar Sesión',
                        icon: Icons.login_outlined,
                        isLoading: _authController.isLoading,
                        isFullWidth: true,
                        onPressed: _authController.isLoading ? null : _ejecutarLogin,
                      ),
                      const SizedBox(height: 12),
                      CustomOutlineButton(
                        text: 'Continuar como invitado',
                        icon: Icons.person_outline,
                        isFullWidth: true,
                        onPressed: () {
                          setState(() {
                            _modoInvitado = true;
                          });
                        },
                      ),
                    ] else ...[
                      CustomInput(
                        hint: 'Tu nombre',
                        label: 'Nombre o alias',
                        controller: _invitadoController,
                        prefixIcon: Icons.badge_outlined,
                      ),
                      const SizedBox(height: 16),
                      CustomPrimaryButton(
                        text: 'Ingresar',
                        icon: Icons.arrow_forward_outlined,
                        isLoading: _authController.isLoading,
                        isFullWidth: true,
                        onPressed: _authController.isLoading ? null : _ejecutarIngresoInvitado,
                      ),
                      const SizedBox(height: 10),
                      CustomOutlineButton(
                        text: 'Volver al formulario de login',
                        icon: Icons.arrow_back_outlined,
                        isFullWidth: true,
                        onPressed: () {
                          setState(() {
                            _modoInvitado = false;
                          });
                        },
                      ),
                    ],

                    const SizedBox(height: 28),
                    Center(
                      child: Text(
                        LocalStorageService.baseUrl,
                        style: textos.cuerpoPequeno.copyWith(
                          color: colores.secundario,
                          fontSize: 11,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
