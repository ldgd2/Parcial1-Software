import 'package:flutter_test/flutter_test.dart';
import 'package:movil/main.dart';

void main() {
  testWidgets('Carga inicial del Visor Movil', (WidgetTester tester) async {
    await tester.pumpWidget(const MovilVisorApp());
    expect(find.byType(MovilVisorApp), findsOneWidget);
  });
}
