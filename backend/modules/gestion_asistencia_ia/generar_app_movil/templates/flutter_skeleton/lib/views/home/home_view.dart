import 'package:flutter/material.dart';

class HomeView extends StatelessWidget {
  const HomeView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Panel Principal'),
      ),
      body: const Center(
        child: Text(
          'Módulos generados listos',
          style: TextStyle(color: Color(0xFFF8FAFC)),
        ),
      ),
    );
  }
}

